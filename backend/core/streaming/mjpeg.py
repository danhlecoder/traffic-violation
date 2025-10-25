"""
RTSP Streaming Service - MJPEG streaming từ RTSP/HTTP với YOLO detection
"""

import os
import time
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
from ...utils.database import get_db
from ...utils.logger import stream_logger as logger


def open_capture(src: str) -> Optional[cv2.VideoCapture]:
    """Mở VideoCapture từ URL/file"""
    try:
        cap = cv2.VideoCapture(src)
        if not cap.isOpened():
            return None
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

    # ROI state tracker cho violation detection
    roi_state_tracker = None
    if enable_violation_detection and camera_id and roi:
        roi_state_tracker = get_roi_state_tracker(
            camera_id,
            cleanup_timeout=settings.ROI_STATE_CLEANUP_TIMEOUT
        )

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
        skip_frames = settings.STREAM_SKIP_FRAMES
        frame_count = 0

        while True:
            # Clear buffer - đọc và bỏ frame cũ để giảm lag
            for _ in range(skip_frames):
                cap.grab()

            ret, frame = cap.read()
            frame_count += 1

            if not ret:
                logger.warning(f"Không đọc được frame (frame {frame_count}), tiếp tục...")
                time.sleep(0.05)

                # Nếu liên tục lỗi quá nhiều, dừng stream
                if frame_count > 100 and frame_count % 50 == 0:
                    logger.error("Quá nhiều lỗi đọc frame, dừng stream")
                    break

                continue

            # Throttle FPS (giảm sleep time)
            current_time = time.time()
            elapsed = current_time - last_frame_time

            if elapsed < delay:
                sleep_time = min(delay - elapsed, 0.01)  # Max sleep 10ms
                time.sleep(sleep_time)

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

            # Chạy YOLO detection nếu được bật
            if detector is not None and enable_detection:
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

                    # Object tracking: Gán track_id CHỈ cho VEHICLES (không track license_plate, helmet, no_helmet, traffic_lights)
                    if object_tracker:
                        # Chỉ track vehicles chính (xe)
                        vehicle_classes = {"bus", "car", "motorcycle", "truck"}
                        vehicles_to_track = [d for d in detections if d["class_name"] in vehicle_classes]

                        # Track vehicles và gán track_id
                        if vehicles_to_track:
                            tracked_vehicles = object_tracker.update(vehicles_to_track)

                            # Merge lại: tracked vehicles + objects không cần track (plates, helmets, lights)
                            non_vehicle_classes = {"license_plate", "helmet", "no_helmet", "light_red", "light_green", "light_yellow"}
                            non_vehicles = [d for d in detections if d["class_name"] in non_vehicle_classes]
                            detections = tracked_vehicles + non_vehicles
                        # else: không có vehicles, giữ nguyên detections

                    # Đếm mật độ phương tiện TỪ TẤT CẢ DETECTIONS (trước khi filter)
                    vehicle_count = count_vehicles(detections)

                    # Lọc detections theo ROI (nếu có)
                    detections_to_draw = detections
                    if roi:
                        h, w = frame.shape[:2]
                        detections_to_draw = filter_detections_by_roi(detections, roi, w, h)

                    # Phát hiện vi phạm - Entry/Exit based
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
                                is_in_roi = det in detections_to_draw

                                # Update state và check entry event
                                is_entry = roi_state_tracker.update(track_id, is_in_roi)

                                # Chỉ tạo violation khi ENTRY event
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
                                            db = get_db()
                                            save_violation_to_db(violation, db)
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
                                # Convert normalized → pixel
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
                                for det in detections:
                                    if det["class_name"] not in VEHICLE_CLASSES:
                                        continue

                                    track_id = det.get("track_id")
                                    if not track_id:
                                        # Bỏ qua xe chưa được track (bình thường với detection mới)
                                        continue

                                    # Extract y2
                                    bbox = det.get("bbox")
                                    if not bbox or len(bbox) != 4:
                                        continue
                                    _, _, _, y2 = bbox

                                    # Filter: chỉ check xe gần stopline
                                    if abs(y2 - stopline_y) > 30:
                                        continue

                                    # Check crossing
                                    is_crossing = stopline_detector.check_crossing(
                                        track_id=track_id,
                                        bbox=det["bbox"],
                                        stopline_y=stopline_y
                                    )

                                    # Ghi hình nếu phát hiện crossing
                                    if is_crossing:
                                        record_count += 1

                                        # Tìm plate (nếu có)
                                        plate_det = None
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

                                        # Tạo record
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
                                            violation["violation_type"] = "stopline_crossing"
                                            try:
                                                db = get_db()
                                                save_violation_to_db(violation, db)
                                            except Exception as e:
                                                logger.error(f"Lỗi lưu record: {e}")

                        except Exception as e:
                            logger.error(f"Lỗi stopline detection: {e}")

                    # Vẽ detections
                    # 1. Vẽ vehicles/plates trong ROI
                    frame = detector.draw_detections(frame, detections_to_draw)
                    
                    # 2. Vẽ riêng đèn giao thông (luôn hiển thị, không filter ROI)
                    traffic_lights = [d for d in detections if d["class_name"] in {"light_red", "light_green", "light_yellow"}]
                    if traffic_lights:
                        frame = detector.draw_detections(frame, traffic_lights)

                    # Cập nhật cache cho camera này
                    update_vehicle_count(src, vehicle_count)

                    # Update density cache
                    if frame_count % 100 == 0 and detections:
                        density_info = get_vehicle_density_info(vehicle_count)

                except Exception as e:
                    logger.error(f"Lỗi khi chạy detection: {e}", exc_info=True)
                    # Tiếp tục stream với frame gốc

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
