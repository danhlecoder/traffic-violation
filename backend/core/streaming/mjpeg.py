"""
RTSP Streaming Service - MJPEG streaming từ RTSP/HTTP với YOLO detection
"""

import time
from datetime import datetime, timezone, timedelta
from typing import Generator, Optional
import cv2

from ...config.config import settings
from ..detection.yolo import get_yolo_detector
from ..tracking.vehicle_tracker import get_tracker, reset_tracker
from ..tracking.stopline_tracker import get_stopline_crossing_detector
from ..tracking.trajectory_tracker import get_trajectory_tracker
from ..tracking.trajectory_drawer import get_trajectory_drawer
from ..analysis.density import count_vehicles, get_vehicle_density_info, update_vehicle_count
from ..constants import VEHICLE_CLASSES
from ...utils.logger import stream_logger as logger
from .frame_processor import validate_frame, prepare_detection_frame, scale_bboxes_back
from .violation_handler import process_stopline_violations
from ..violations.speed import SpeedViolationRecorder
from ..violations.red_light import RedLightViolationRecorder
from ..violations.helmet import NoHelmetViolationRecorder
from ...api.clients.mongodb_service import get_mongodb_service
from ...utils.violations import normalize_stopline_y



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
    camera_id: Optional[str] = None,
    camera_name: Optional[str] = None,
    location: Optional[str] = None,
    enable_violation_detection: bool = True,
    stopline: Optional[dict] = None
) -> Generator[bytes, None, None]:
    """
    Generator tạo MJPEG stream từ nguồn RTSP/HTTP với YOLO detection

    Args:
        src: URL nguồn video
        fps: FPS mục tiêu, mặc định lấy từ settings
        jpeg_quality: Chất lượng JPEG (10-95), mặc định lấy từ settings
        enable_detection: Bật/tắt YOLO detection
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
            min_hits=settings.TRACKER_MIN_HITS,
            center_distance_threshold=settings.TRACKER_CENTER_DISTANCE_PX,
            init_grace_frames=settings.TRACKER_INIT_GRACE_FRAMES
        )
        logger.info(f"✓ Object tracker initialized for camera {camera_id} (IOU={settings.TRACKER_IOU_THRESHOLD}, min_hits={settings.TRACKER_MIN_HITS})")
    else:
        logger.warning(f"⚠️  Object tracker NOT initialized - enable_detection={enable_detection}, camera_id={camera_id}")

    # Trajectory tracker & drawer
    trajectory_tracker = None
    trajectory_drawer = None
    if settings.TRAJECTORY_ENABLED and camera_id:
        trajectory_tracker = get_trajectory_tracker(
            camera_id,
            max_trajectory_points=settings.TRAJECTORY_MAX_POINTS,
            cleanup_timeout=settings.TRAJECTORY_CLEANUP_TIMEOUT
        )
        trajectory_drawer = get_trajectory_drawer(
            line_thickness=settings.TRAJECTORY_LINE_THICKNESS,
            point_radius=settings.TRAJECTORY_POINT_RADIUS,
            arrow_length=settings.TRAJECTORY_ARROW_LENGTH,
            show_speed=settings.TRAJECTORY_SHOW_SPEED,
            show_track_id=settings.TRAJECTORY_SHOW_TRACK_ID,
            fade_effect=settings.TRAJECTORY_FADE_EFFECT,
            speed_in_kmh=settings.TRAJECTORY_SPEED_IN_KMH,
            pixels_per_meter=settings.PIXELS_PER_METER
        )
        trajectory_drawer.pixels_per_meter = settings.PIXELS_PER_METER

    # Stopline crossing detector & speed/red-light recorders
    stopline_detector = None
    speed_recorder = None
    redlight_recorder = None
    helmet_recorder = None
    if enable_violation_detection and camera_id:
        if stopline:
            stopline_detector = get_stopline_crossing_detector(camera_id)
        # Khởi tạo speed recorder (không phụ thuộc stopline)
        try:
            speed_recorder = SpeedViolationRecorder(
                camera_id=camera_id,
                camera_name=camera_name,
                location=location,
            )
        except Exception as e:
            logger.error(f"Lỗi khởi tạo SpeedViolationRecorder: {e}")
        # Khởi tạo red light recorder (cần stopline để so sánh toạ độ)
        try:
            redlight_recorder = RedLightViolationRecorder(
                camera_id=camera_id,
                camera_name=camera_name,
                location=location,
            )
        except Exception as e:
            logger.error(f"Lỗi khởi tạo RedLightViolationRecorder: {e}")
        # Khởi tạo recorder không đội mũ bảo hiểm
        try:
            helmet_recorder = NoHelmetViolationRecorder(
                camera_id=camera_id,
                camera_name=camera_name,
                location=location,
            )
        except Exception as e:
            logger.error(f"Lỗi khởi tạo NoHelmetViolationRecorder: {e}")

    cap = open_capture(src)

    mongo_service = get_mongodb_service() if camera_id else None
    camera_min_confidence: Optional[float] = None
    last_camera_rules_fetch = 0.0
    camera_rules_refresh = float(settings.MONGO_CAMERA_CACHE_TTL or 0.0)
    stopline_y_pixels: Optional[float] = None

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

        # Reset tracker ID khi không có xe trong một khoảng thời gian
        idle_no_vehicle_frames = 0
        idle_frames_threshold = max(1, int((fps or settings.STREAM_DEFAULT_FPS) * max(0.1, settings.TRACKER_RESET_IDLE_SECONDS)))

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

            # Validate frame trước khi xử lý (sử dụng hàm utility)
            is_valid, dimensions = validate_frame(frame)
            if not is_valid:
                continue

            if stopline and stopline_y_pixels is None:
                stopline_y_pixels = normalize_stopline_y(stopline, frame.shape[0])

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
                        # Sử dụng hàm utility để chuẩn bị frame detection
                        detection_width = settings.STREAM_DETECTION_WIDTH
                        det_frame, scale_back = prepare_detection_frame(frame, detection_width)

                        # Lấy minConfidence từ camera detection_rules (nếu có), mặc định dùng từ settings
                        min_confidence = camera_min_confidence
                        if mongo_service and camera_id:
                            now_mono = time.monotonic()
                            needs_refresh = (
                                min_confidence is None
                                or camera_rules_refresh == 0.0
                                or (now_mono - last_camera_rules_fetch) >= camera_rules_refresh
                            )
                            if needs_refresh:
                                last_camera_rules_fetch = now_mono
                                try:
                                    camera = mongo_service.get_camera(camera_id)
                                    rules = camera.get("detection_rules") if camera else None
                                    min_conf_val = rules.get("minConfidence") if rules else None
                                    camera_min_confidence = float(min_conf_val) if min_conf_val is not None else None
                                    min_confidence = camera_min_confidence
                                except Exception as e:
                                    camera_min_confidence = None
                                    logger.debug(f"Không lấy được detection_rules từ camera {camera_id}: {e}")
                            else:
                                min_confidence = camera_min_confidence

                        # Detect trên frame đã chuẩn bị với minConfidence từ camera (nếu có)
                        detections = detector.detect(det_frame, conf=min_confidence)

                        # Scale bbox về kích thước frame gốc
                        scale_bboxes_back(detections, scale_back)

                        # Log detection results mỗi 30 frames để giảm log overhead
                        if frame_count % 30 == 0:
                            vehicle_dets = [d for d in detections if d["class_name"] in VEHICLE_CLASSES]
                            logger.info(f"📊 Frame {frame_count}: Detected {len(detections)} objects ({len(vehicle_dets)} vehicles) - Enable detection: {enable_detection}")

                    except Exception as e:
                        logger.error(f"Lỗi khi detect: {e}")
                        detections = []

            # Object tracking: Gán track_id CHỈ cho VEHICLES (không track license_plate, helmet, no_helmet, traffic_lights)
            if object_tracker and detections:
                # Chỉ track vehicles chính (xe)
                vehicles_to_track = [d for d in detections if d["class_name"] in VEHICLE_CLASSES]

                if vehicles_to_track:
                    tracked_vehicles = object_tracker.update(vehicles_to_track)

                    # Gán track_id trực tiếp từ tracker - đảm bảo mọi vehicle đều có track_id
                    tracked_count = 0
                    for idx, det in enumerate(vehicles_to_track):
                        track_info = tracked_vehicles[idx] if idx < len(tracked_vehicles) else None
                        track_id = track_info.get("track_id") if track_info else None
                        # Đảm bảo mọi vehicle đều có track_id
                        if track_id is None:
                            # Nếu không có track_id, tìm trong tracked_vehicles bằng cách match bbox
                            for tv in tracked_vehicles:
                                if tv.get("bbox") == det.get("bbox") or abs(tv.get("bbox", [0])[0] - det.get("bbox", [0])[0]) < 5:
                                    track_id = tv.get("track_id")
                                    break
                        det["track_id"] = track_id
                        if track_id is not None:
                            tracked_count += 1

                    # Cập nhật trajectory tracker TRƯỚC khi check violation
                    # Đảm bảo trajectory có đủ điểm để tính tốc độ
                    if trajectory_tracker:
                        for det in vehicles_to_track:
                            track_id = det.get("track_id")
                            bbox = det.get("bbox")
                            if track_id is None or not bbox or len(bbox) != 4:
                                continue
                            # Update trajectory với điểm mới từ frame hiện tại
                            trajectory_tracker.update(
                                track_id,
                                (bbox[0], bbox[1], bbox[2], bbox[3])
                            )

                    # Log tracking info mỗi 30 frames để giảm log overhead
                    if frame_count % 30 == 0:
                        logger.info(
                            f"🎯 Frame {frame_count}: Detected {len(detections)} objects, "
                            f"{len(vehicles_to_track)} vehicles → {tracked_count} có track_id"
                        )

                    vehicle_count = tracked_count
                else:
                    # Không có xe trong frame này, vẫn gọi update([]) để tăng bộ đếm miss
                    object_tracker.update([])
                    vehicle_count = 0

            # Cơ chế reset tracker khi không có xe trong một khoảng liên tiếp (để giải phóng bộ nhớ)
            if object_tracker:
                if vehicle_count == 0:
                    idle_no_vehicle_frames += 1
                else:
                    idle_no_vehicle_frames = 0

                if settings.TRACKER_RESET_ON_IDLE and idle_no_vehicle_frames >= idle_frames_threshold:
                    logger.info("🔄 Không có phương tiện trong một thời gian, reset tracker để giải phóng bộ nhớ")
                    try:
                        reset_tracker(camera_id)
                    except Exception as _:
                        pass
                    # Dọn trajectory cùng lúc để không vẽ vệt cũ
                    try:
                        if trajectory_tracker:
                            trajectory_tracker.clear()
                    except Exception:
                        pass
                    idle_no_vehicle_frames = 0

            # Chủ động loại bỏ trajectory đã hết hạn để tránh hiển thị "vệt ma"
            if trajectory_tracker:
                prune_window = max(settings.TRAJECTORY_ACTIVE_SECONDS * 2.0, 1.0)
                trajectory_tracker.prune_inactive(prune_window)

            # Không filter ROI - detect tất cả xe
            detections_to_draw = detections

            # Ghi hình phương tiện vượt stopline (sử dụng hàm utility)
            if stopline_detector and stopline:
                _ = process_stopline_violations(
                    frame=frame,
                    detections=detections_to_draw,
                    stopline=stopline,
                    stopline_detector=stopline_detector,
                    detector=detector,
                    camera_id=camera_id,
                    camera_name=camera_name,
                    location=location,
                    trajectory_tracker=trajectory_tracker
                )

            # Ghi nhận vi phạm tốc độ (nếu bật và có tracker)
            if speed_recorder and trajectory_tracker and detections_to_draw:
                try:
                    speed_recorder.process(
                        frame=frame,
                        detections=detections_to_draw,
                        detector=detector,
                        stopline=stopline,
                    )
                except Exception as e:
                    logger.error(f"Lỗi khi xử lý vi phạm tốc độ: {e}")

            # Ghi nhận vi phạm vượt đèn đỏ
            if redlight_recorder and stopline and detections_to_draw:
                try:
                    redlight_recorder.process(
                        frame=frame,
                        detections=detections_to_draw,
                        stopline=stopline,
                        detector=detector,
                    )
                except Exception as e:
                    logger.error(f"Lỗi khi xử lý vi phạm đèn đỏ: {e}")

            # Ghi nhận vi phạm không đội mũ bảo hiểm
            if helmet_recorder and detections_to_draw:
                try:
                    helmet_recorder.process(
                        frame=frame,
                        detections=detections_to_draw,
                        detector=detector,
                    )
                except Exception as e:
                    logger.error(f"Lỗi khi xử lý vi phạm không đội mũ bảo hiểm: {e}")

            # Vẽ detections - CHỈ vẽ detections TRONG ROI
            if detector and detections_to_draw:
                frame = detector.draw_detections(frame, detections_to_draw)
            update_vehicle_count(src, vehicle_count)
            if frame_count % 100 == 0 and detections:
                density_info = get_vehicle_density_info(vehicle_count)

            # Vẽ trajectory sau khi có track và detection
            if trajectory_tracker and trajectory_drawer:
                frame = trajectory_drawer.draw_all_trajectories(
                    frame,
                    trajectory_tracker,
                    active_only=True,
                    active_seconds=settings.TRAJECTORY_ACTIVE_SECONDS,
                    stopline_y=stopline_y_pixels,
                    pixels_per_meter=settings.PIXELS_PER_METER,
                )

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
