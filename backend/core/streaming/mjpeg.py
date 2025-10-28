"""
RTSP Streaming Service - MJPEG streaming từ RTSP/HTTP với YOLO detection
"""

import time
from datetime import datetime, timezone, timedelta
from typing import Generator, Optional
import cv2

from ...config.config import settings
from ..detection.yolo import get_yolo_detector
from ..detection.filters import filter_detections_by_roi
from ..tracking.vehicle_tracker import get_tracker
from ..tracking.roi_entry_tracker import get_roi_state_tracker
from ..tracking.stopline_tracker import get_stopline_crossing_detector
from ..violations.creator import create_violation_record
from ..violations.repository import save_violation_to_db
from ..analysis.density import count_vehicles, get_vehicle_density_info, update_vehicle_count
from ...utils.logger import stream_logger as logger


def open_capture(src: str) -> Optional[cv2.VideoCapture]:
    """Mở VideoCapture từ URL/file với timeout"""
    try:
        cap = cv2.VideoCapture(src)
        if not cap.isOpened():
            return None
        
        # Set timeout properties để tránh hang
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)  # 5s timeout khi connect
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)  # 5s timeout khi read
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer size = 1 để giảm lag
        
        return cap
    except Exception as e:
        logger.error(f"Lỗi mở capture: {e}")
        return None


def generate_mjpeg(
    src: str,
    fps: Optional[int] = None,
    jpeg_quality: Optional[int] = None,
    enable_detection: bool = True,
    roi: Optional[list] = None,
    stopline: Optional[dict] = None,
    camera_id: Optional[str] = None,
    camera_name: Optional[str] = None,
    location: Optional[str] = None,
    enable_violation_detection: bool = True
) -> Generator[bytes, None, None]:
    """
    Generator tạo MJPEG stream từ nguồn RTSP/HTTP với YOLO detection

    Args:
        src: URL nguồn video
        fps: FPS mục tiêu, mặc định lấy từ settings
        jpeg_quality: Chất lượng JPEG (10-95), mặc định lấy từ settings
        enable_detection: Bật/tắt YOLO detection
        roi: ROI normalized [{x, y}, ...] để filter bbox (None = hiện tất cả)
        stopline: Stopline dict với 'y' position (pixel)
        camera_id: ID camera (để lưu violations)
        camera_name: Tên camera
        location: Vị trí camera
        enable_violation_detection: Bật/tắt phát hiện vi phạm

    Yields:
        Bytes của multipart MJPEG stream
    """
    # Sử dụng giá trị mặc định từ settings nếu không được truyền vào
    if fps is None:
        fps = settings.STREAM_DEFAULT_FPS
    if jpeg_quality is None:
        jpeg_quality = settings.STREAM_DEFAULT_QUALITY

    # Chuẩn bị các tham số
    boundary = b"--frame"
    delay = 1.0 / max(1, fps)

    detector = None
    if enable_detection:
        try:
            detector = get_yolo_detector()
        except Exception as e:
            logger.warning(f"YOLO init failed: {e}")

    # Object tracker cho camera này
    object_tracker = None
    if enable_detection and camera_id:
        object_tracker = get_tracker(
            camera_id,
            iou_threshold=settings.TRACKER_IOU_THRESHOLD,
            max_age=settings.TRACKER_MAX_AGE,
            min_hits=settings.TRACKER_MIN_HITS
        )
        logger.info(f"✓ Object tracker initialized for camera {camera_id} (IOU={settings.TRACKER_IOU_THRESHOLD}, min_hits={settings.TRACKER_MIN_HITS})")
    else:
        logger.warning(f"⚠️  Object tracker NOT initialized - enable_detection={enable_detection}, camera_id={camera_id}")

    # ROI state tracker cho violation detection
    # Chạy ngay cả khi không có ROI config (track tất cả phương tiện)
    roi_state_tracker = None
    if enable_violation_detection and camera_id:
        roi_state_tracker = get_roi_state_tracker(
            camera_id,
            cleanup_timeout=settings.ROI_STATE_CLEANUP_TIMEOUT
        )
        if not roi:
            logger.info(f"🔍 Violation detection mode: FULL FRAME (không có ROI config)")

    # Stopline crossing detector
    stopline_detector = None
    if enable_violation_detection and camera_id and stopline:
        stopline_detector = get_stopline_crossing_detector(camera_id)

    cap = open_capture(src)

    if cap is None:
        logger.error("Không thể mở nguồn video, trả về frame rỗng")
        # Yield empty frame để client có thể xử lý lỗi
        yield boundary + b"\r\nContent-Type: image/jpeg\r\n\r\n" + b"" + b"\r\n"
        return

    try:
        last_frame_time = 0.0
        skip_counter = 0
        skip_frames = 0  # REALTIME: Không skip frames nào
        frame_count = 0
        detection_frame_counter = 0  # Counter for detection skip
        DETECTION_SKIP_FRAMES = 0  # REALTIME: Detect MỌI frame
        consecutive_errors = 0  # Đếm lỗi liên tiếp
        MAX_CONSECUTIVE_ERRORS = 10  # Max 10 lỗi liên tiếp (0.5s) - Reconnect nhanh hơn

        while True:
            # Clear buffer - đọc và bỏ frame cũ để giảm lag
            for _ in range(skip_frames):
                cap.grab()

            ret, frame = cap.read()
            frame_count += 1

            if not ret:
                consecutive_errors += 1
                logger.warning(f"Không đọc được frame (frame {frame_count}), lỗi liên tiếp: {consecutive_errors}/{MAX_CONSECUTIVE_ERRORS}")
                
                # Nếu lỗi liên tiếp quá nhiều, thử reconnect
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    logger.error("Quá nhiều lỗi liên tiếp, thử reconnect...")
                    cap.release()
                    time.sleep(0.5)  # Giảm từ 1s xuống 0.5s
                    cap = open_capture(src)
                    if cap is None:
                        logger.error("Reconnect thất bại, dừng stream")
                        break
                    logger.info("✓ Reconnect thành công")
                    consecutive_errors = 0
                    continue
                
                time.sleep(0.05)
                continue
            
            # Reset error counter khi đọc frame thành công
            consecutive_errors = 0

            # REALTIME: Không throttle FPS, xử lý ngay
            last_frame_time = time.time()

            # Validate frame trước khi xử lý
            if frame is None or frame.size == 0:
                logger.warning("Frame rỗng hoặc None, bỏ qua")
                continue

            # Kiểm tra frame có bị corrupted không
            try:
                h, w = frame.shape[:2]
                if h <= 0 or w <= 0:
                    logger.warning(f"Frame có kích thước invalid: {w}x{h}")
                    continue

                # Kiểm tra frame có pixel values hợp lệ
                mean_val = frame.mean()
                if mean_val < 5 or mean_val > 250:
                    continue

            except Exception as e:
                logger.warning(f"Lỗi khi validate frame: {e}")
                continue

            # Initialize vehicle count
            vehicle_count = 0
            
            # Chạy YOLO detection nếu được bật (skip frames để giảm API calls)
            detections = []
            if detector is not None and enable_detection:
                # Only detect every Nth frame to reduce API calls to YOLO service
                should_detect = (detection_frame_counter % (DETECTION_SKIP_FRAMES + 1) == 0)
                detection_frame_counter += 1
                
                if should_detect:
                    try:
                        # Resize frame nhỏ hơn trước khi detect để tăng tốc
                        detection_width = settings.STREAM_DETECTION_WIDTH
                        if detection_width > 0:
                            h, w = frame.shape[:2]
                            if w > detection_width:
                                scale = detection_width / w
                                new_h = int(h * scale)
                                det_frame = cv2.resize(frame, (detection_width, new_h), interpolation=cv2.INTER_LINEAR)

                                # Detect trên frame nhỏ
                                detections = detector.detect(det_frame)

                                # Scale bbox về kích thước gốc
                                scale_back = w / detection_width
                                for det in detections:
                                    det["bbox"] = [coord * scale_back for coord in det["bbox"]]
                            else:
                                detections = detector.detect(frame)
                        else:
                            detections = detector.detect(frame)
                        
                        # Log detection results every 10 frames (để debug dễ hơn)
                        if frame_count % 10 == 0:
                            vehicle_dets = [d for d in detections if d["class_name"] in {"bus", "car", "motorcycle", "truck"}]
                            logger.info(f"📊 Frame {frame_count}: Detected {len(detections)} objects ({len(vehicle_dets)} vehicles) - Enable detection: {enable_detection}")

                    except Exception as e:
                        logger.error(f"Lỗi khi detect: {e}")
                        detections = []

            # Object tracking: Gán track_id CHỈ cho VEHICLES (không track license_plate, helmet, no_helmet, traffic_lights)
            if object_tracker and detections:
                # Chỉ track vehicles chính (xe)
                vehicle_classes = {"bus", "car", "motorcycle", "truck"}
                vehicles_to_track = [d for d in detections if d["class_name"] in vehicle_classes]
                
                if vehicles_to_track:
                    tracked_vehicles = object_tracker.update(vehicles_to_track)
                    
                    # Gán track_id vào detections
                    tracked_count = 0
                    for det in detections:
                        if det["class_name"] not in vehicle_classes:
                            continue
                        bbox = det.get("bbox")
                        if not bbox or len(bbox) != 4:
                            continue
                        # Match bbox với IoU để robust hơn
                        best_match = None
                        best_iou = 0.3  # Threshold tối thiểu
                        
                        for track in tracked_vehicles:
                            track_bbox = track["bbox"]
                            # Calculate IoU (Intersection over Union)
                            x1_i = max(bbox[0], track_bbox[0])
                            y1_i = max(bbox[1], track_bbox[1])
                            x2_i = min(bbox[2], track_bbox[2])
                            y2_i = min(bbox[3], track_bbox[3])
                            
                            if x2_i > x1_i and y2_i > y1_i:
                                intersection = (x2_i - x1_i) * (y2_i - y1_i)
                                area1 = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                                area2 = (track_bbox[2] - track_bbox[0]) * (track_bbox[3] - track_bbox[1])
                                union = area1 + area2 - intersection
                                iou = intersection / union if union > 0 else 0
                                
                                if iou > best_iou:
                                    best_iou = iou
                                    best_match = track
                        
                        if best_match:
                            det["track_id"] = best_match["track_id"]
                            tracked_count += 1
                    
                    # Log tracking info mỗi 10 frames để debug chi tiết hơn
                    if frame_count % 10 == 0:
                        logger.info(f"🎯 Frame {frame_count}: Detected {len(detections)} objects, {len(vehicles_to_track)} vehicles → {tracked_count} có track_id (total active tracks: {len(tracked_vehicles)})")
                    
                    vehicle_count = len(tracked_vehicles)

            # Lọc detections theo ROI (nếu có)
            detections_to_draw = detections
            if roi:
                h, w = frame.shape[:2]
                detections_to_draw = filter_detections_by_roi(detections, roi, w, h)
            # Nếu không có ROI, hiển thị TẤT CẢ detections
            else:
                detections_to_draw = detections

            # Phát hiện vi phạm - ROI Entry/Exit based
            if roi_state_tracker:
                try:
                    VEHICLE_CLASSES = {"bus", "car", "motorcycle", "truck"}

                    # Update state cho TẤT CẢ tracked vehicles
                    for det in detections:
                        if det["class_name"] not in VEHICLE_CLASSES:
                            continue

                        track_id = det.get("track_id")
                        if not track_id:
                            continue

                        # Check if vehicle trong ROI
                        # Nếu không có ROI config: tất cả đều được coi là "in ROI"
                        if roi:
                            is_in_roi = det in detections_to_draw
                        else:
                            # Không có ROI: track tất cả vehicles
                            is_in_roi = True

                        # Update state và check entry event
                        is_entry = roi_state_tracker.update(track_id, is_in_roi)

                        # Chỉ tạo ROI ENTRY violation khi KHÔNG có stopline config
                        # Nếu có stopline → chỉ dùng stopline crossing violations
                        if stopline:
                            continue  # Skip ROI entry violations, chờ stopline crossing
                        
                        # Tạo violation khi ENTRY event (chỉ khi không có stopline)
                        if is_entry and roi_state_tracker.should_create_violation(track_id):
                            # Tìm plate (nếu có)
                            plate_det = None
                            plates = [d for d in detections if d["class_name"] == "license_plate"]
                            for plate in plates:
                                plate_bbox = plate.get("bbox")
                                if not plate_bbox or len(plate_bbox) < 4:
                                    continue
                                if not all(isinstance(x, (int, float)) for x in plate_bbox):
                                    continue
                                px1, py1, px2, py2 = plate_bbox
                                if px1 < 0 or py1 < 0 or px2 < 0 or py2 < 0:
                                    continue
                                pcx, pcy = (px1 + px2) / 2, (py1 + py2) / 2
                                det_bbox = det.get("bbox")
                                if not det_bbox or len(det_bbox) < 4:
                                    continue
                                if not all(isinstance(x, (int, float)) for x in det_bbox):
                                    continue
                                vx1, vy1, vx2, vy2 = det_bbox
                                if vx1 < 0 or vy1 < 0 or vx2 < 0 or vy2 < 0:
                                    continue
                                if vx1 <= pcx <= vx2 and vy1 <= pcy <= vy2:
                                    plate_det = plate
                                    break

                            # Tạo violation record
                            violation = create_violation_record(
                                frame=frame.copy(),
                                vehicle_det=det,
                                plate_det=plate_det,
                                track_id=track_id,
                                camera_id=camera_id,
                                camera_name=camera_name,
                                location=location
                            )

                            # Lưu vào DB
                            if violation:
                                try:
                                    save_violation_to_db(violation)
                                    # Mark đã tạo violation
                                    roi_state_tracker.mark_violation_created(track_id)
                                except Exception as e:
                                    logger.error(f"Lỗi lưu violation: {e}")

                except Exception as e:
                    logger.error(f"Lỗi detect violation (ROI): {e}")

            # Ghi hình phương tiện vượt stopline
            if stopline_detector and stopline:
                try:
                    VEHICLE_CLASSES = {"bus", "car", "motorcycle", "truck"}

                    if not isinstance(stopline, dict) or "y" not in stopline:
                        logger.error(f"Stopline format sai: {type(stopline)}")
                    else:
                        stopline_y_raw = float(stopline["y"])
                        is_normalized = stopline.get("is_normalized", False)

                        if is_normalized:
                            frame_height = frame.shape[0]
                            stopline_y = stopline_y_raw * frame_height
                            if frame_count == 1:
                                logger.info(f"Stopline: {stopline_y_raw:.3f} → {stopline_y:.1f}px")
                        else:
                            stopline_y = stopline_y_raw
                            if frame_count == 1:
                                logger.info(f"Stopline: {stopline_y:.1f}px")

                        record_count = 0
                        # CHỈ xử lý xe TRONG ROI (detections_to_draw đã được lọc)
                        for det in detections_to_draw:
                            if det["class_name"] not in VEHICLE_CLASSES:
                                continue
                            track_id = det.get("track_id")
                            if not track_id:
                                continue
                            bbox = det.get("bbox")
                            if not bbox or len(bbox) != 4:
                                continue
                            _, _, _, y2 = bbox
                            # Vùng detection: stopline_y ± STOPLINE_DETECTION_RANGE (20px)
                            # Bắt cả xe đang tiến vào (y2 < stopline) VÀ xe đang vượt qua (y2 > stopline)
                            # Tổng vùng: 40px (20px trước + 20px sau stopline)
                            detection_min = stopline_y - settings.STOPLINE_DETECTION_RANGE
                            detection_max = stopline_y + settings.STOPLINE_DETECTION_RANGE
                            
                            # Chỉ check xe trong vùng detection
                            if not (detection_min <= y2 <= detection_max):
                                continue
                            
                            # Log khi xe trong vùng detection
                            distance_to_stopline = y2 - stopline_y
                            logger.info(f"🚗 Track {track_id}: y2={y2:.1f}px, stopline={stopline_y:.1f}px, distance={distance_to_stopline:+.1f}px (vùng: {detection_min:.1f} - {detection_max:.1f})")
                            
                            is_crossing = stopline_detector.check_crossing(
                                track_id=track_id,
                                bbox=det["bbox"],
                                stopline_y=stopline_y
                            )
                            if is_crossing:
                                record_count += 1
                                plate_det = None
                                
                                # Step 1: Tìm plate trong detections từ video
                                plates = [d for d in detections if d["class_name"] == "license_plate"]
                                for plate in plates:
                                    plate_bbox = plate.get("bbox")
                                    if not plate_bbox or len(plate_bbox) != 4:
                                        continue
                                    px1, py1, px2, py2 = plate_bbox
                                    pcx, pcy = (px1 + px2) / 2, (py1 + py2) / 2
                                    vx1, vy1, vx2, vy2 = det["bbox"]
                                    if vx1 <= pcx <= vx2 and vy1 <= pcy <= vy2:
                                        plate_det = plate
                                        break
                                
                                # Step 2: Nếu không tìm thấy plate → Detect lại trên ảnh xe
                                if plate_det is None and detector:
                                    try:
                                        vx1, vy1, vx2, vy2 = det["bbox"]
                                        vx1, vy1, vx2, vy2 = int(vx1), int(vy1), int(vx2), int(vy2)
                                        
                                        # Crop ảnh xe
                                        h, w = frame.shape[:2]
                                        vx1 = max(0, vx1)
                                        vy1 = max(0, vy1)
                                        vx2 = min(w, vx2)
                                        vy2 = min(h, vy2)
                                        
                                        vehicle_crop = frame[vy1:vy2, vx1:vx2]
                                        
                                        if vehicle_crop.size > 0:
                                            # Detect plate trên ảnh xe (dùng best1.pt)
                                            crop_detections = detector.detect(
                                                vehicle_crop,
                                                conf=settings.YOLO_CONFIDENCE,
                                                iou=settings.YOLO_IOU_THRESHOLD
                                            )
                                            
                                            # Tìm plate trong crop_detections
                                            for crop_det in crop_detections:
                                                if crop_det.get("class_name") == "license_plate":
                                                    # Convert bbox từ crop coordinate → frame coordinate
                                                    cx1, cy1, cx2, cy2 = crop_det["bbox"]
                                                    plate_det = {
                                                        "bbox": [
                                                            cx1 + vx1,  # x1 frame
                                                            cy1 + vy1,  # y1 frame
                                                            cx2 + vx1,  # x2 frame
                                                            cy2 + vy1   # y2 frame
                                                        ],
                                                        "confidence": crop_det["confidence"],
                                                        "class_name": "license_plate"
                                                    }
                                                    logger.info(f"✓ Detected plate on vehicle crop: conf={crop_det['confidence']:.2f}")
                                                    break
                                    except Exception as e:
                                        logger.warning(f"Không detect được plate trên ảnh xe: {e}")
                                violation = create_violation_record(
                                    frame=frame.copy(),
                                    vehicle_det=det,
                                    plate_det=plate_det,
                                    track_id=track_id,
                                    camera_id=camera_id,
                                    camera_name=camera_name,
                                    location=location
                                )
                                if violation:
                                    violation["violation_type"] = "stopline_crossing"
                                    try:
                                        save_violation_to_db(violation)
                                        # Mark đã tạo violation để không tạo duplicate
                                        roi_state_tracker.mark_violation_created(track_id)
                                    except Exception as e:
                                        logger.error(f"Lỗi lưu record: {e}")
                except Exception as e:
                    logger.error(f"Lỗi stopline detection: {e}")

            # Vẽ detections - CHỈ vẽ detections TRONG ROI
            if detector and detections_to_draw:
                frame = detector.draw_detections(frame, detections_to_draw)
            update_vehicle_count(src, vehicle_count)
            if frame_count % 100 == 0 and detections:
                density_info = get_vehicle_density_info(vehicle_count)

            # Vẽ thông tin vị trí và thời gian ở góc trái trên
            if location or camera_name:
                # Vị trí (dòng 1)
                text_location = location or camera_name or "Unknown"
                cv2.putText(
                    frame,
                    text_location,
                    (10, 30),  # Góc trái trên, cách lề 10px, dòng 1
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,  # Font size
                    (255, 255, 255),  # Màu trắng
                    2,  # Độ dày
                    cv2.LINE_AA
                )
                
                # Thời gian (dòng 2) - Giờ Việt Nam (UTC+7)
                vietnam_tz = timezone(timedelta(hours=7))
                current_time = datetime.now(vietnam_tz).strftime("%d-%m-%Y %H:%M:%S")
                cv2.putText(
                    frame,
                    current_time,
                    (10, 60),  # Dòng 2, cách dòng 1 khoảng 30px
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA
                )

            # Validate frame một lần nữa sau detection
            if frame is None or frame.size == 0:
                logger.warning("Frame bị invalid sau detection, bỏ qua")
                continue

            # Encode frame thành JPEG với error handling tốt hơn
            encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)]

            try:
                ok, buffer = cv2.imencode(".jpg", frame, encode_params)

                if not ok or buffer is None:
                    logger.warning("Không thể encode frame, bỏ qua")
                    continue
            except Exception as e:
                logger.error(f"Lỗi khi encode frame: {e}")
                continue

            jpg_bytes: bytes = buffer.tobytes()

            # Yield multipart chunk
            yield (
                boundary
                + b"\r\nContent-Type: image/jpeg"
                + b"\r\nContent-Length: " + str(len(jpg_bytes)).encode()
                + b"\r\n\r\n"
                + jpg_bytes
                + b"\r\n"
            )

    except GeneratorExit:
        pass
    except Exception as e:
        logger.error(f"Lỗi trong quá trình streaming: {e}")
    finally:
        try:
            cap.release()
        except Exception:
            pass
