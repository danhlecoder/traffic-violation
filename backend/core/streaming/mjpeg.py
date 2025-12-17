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
    """Mở VideoCapture từ URL/file với timeout và error handling tốt hơn"""
    try:
        # Dùng CAP_FFMPEG backend để xử lý H.264 tốt hơn
        cap = cv2.VideoCapture(src, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            # Fallback sang default backend
            logger.warning("FFMPEG backend failed, trying default backend")
            cap = cv2.VideoCapture(src)
            if not cap.isOpened():
                return None

        # Timeout settings
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)

        # Buffer size: Tăng lên 3 để xử lý H.264 decode errors
        # (buffer = 1 gây decode error do không đủ frames để decode)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 5)

        # RTSP-specific settings
        if 'rtsp' in str(src).lower():
            try:
                # Tắt auto settings
                cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
                cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)

                # H.264 decode settings
                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))

                # Reduce FPS nếu decode không kịp (giảm load)
                # cap.set(cv2.CAP_PROP_FPS, 15)
            except Exception as e:
                logger.debug(f"Could not set RTSP properties: {e}")

        logger.info(f"✓ VideoCapture opened: backend={cap.getBackendName()}")
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
            fade_effect=False,  # TẮT fade để tránh ghosting
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

    # Khởi tạo biến để tracking
    try:
        last_frame_time = 0.0
        last_yield_time = 0.0  # ✅ Track thời gian yield cuối cùng để throttle FPS
        skip_counter = 0
        # ✅ GIẢM skip_frames từ 2 → 0 để XỬ LÝ ĐẦY ĐỦ HƠN (không bỏ frames)
        # Stream sẽ chạy CHẬM HƠN nhưng phát hiện CHÍNH XÁC HƠN
        skip_frames = 0
        frame_count = 0
        detection_frame_counter = 0
        # DETECT MỌI FRAME (theo yêu cầu user - không bỏ frame)
        DETECTION_SKIP_FRAMES = 0
        consecutive_errors = 0
        MAX_CONSECUTIVE_ERRORS = 10

        # Reset tracker ID khi không có xe trong một khoảng thời gian
        idle_no_vehicle_frames = 0
        idle_frames_threshold = max(1, int((fps or settings.STREAM_DEFAULT_FPS) * max(0.1, settings.TRACKER_RESET_IDLE_SECONDS)))

        while True:
            # TỐI ƯU: Clear buffer - grab và bỏ frame cũ để catch up real-time
            # Giảm lag bằng cách bỏ qua frame cũ trong buffer
            if skip_frames > 0:
                for _ in range(skip_frames):
                    cap.grab()

            ret, frame = cap.read()
            frame_count += 1

            if not ret:
                consecutive_errors += 1

                # Chỉ log mỗi 5 lỗi để giảm spam
                if consecutive_errors % 5 == 0 or consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    logger.warning(f"Không đọc được frame (lỗi liên tiếp: {consecutive_errors}/{MAX_CONSECUTIVE_ERRORS})")

                # Nếu lỗi liên tiếp quá nhiều, thử reconnect
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    logger.error("⚠️ Reconnecting stream...")
                    cap.release()
                    time.sleep(1.0)
                    cap = open_capture(src)
                    if cap is None:
                        logger.error("❌ Reconnect failed")
                        break
                    logger.info("✅ Reconnect OK")
                    consecutive_errors = 0
                    continue

                time.sleep(0.1)  # Tăng delay khi lỗi
                continue

            # Reset error counter khi đọc frame thành công
            consecutive_errors = 0

            # TỐI ƯU: Xử lý ngay không throttle (để real-time)
            last_frame_time = time.time()

            # Validate frame trước khi xử lý (sử dụng hàm utility)
            is_valid, dimensions = validate_frame(frame)
            if not is_valid:
                continue

            if stopline and stopline_y_pixels is None:
                stopline_y_pixels = normalize_stopline_y(stopline, frame.shape[0])

            # Initialize vehicle count
            vehicle_count = 0

            # YOLO detection (skip mỗi N frame để tối ưu hiệu năng)
            detections = []
            if detector is not None and enable_detection:
                # Detect mỗi (DETECTION_SKIP_FRAMES + 1) frame
                # ByteTrack sẽ interpolate tracking giữa các detection
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

                        # Log detection mỗi 120 frames
                        if frame_count % 120 == 0:
                            vehicle_dets = [d for d in detections if d["class_name"] in VEHICLE_CLASSES]
                            logger.info(f"Frame {frame_count}: {len(vehicle_dets)} vehicles")

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

                    # Log tracking mỗi 120 frames
                    if frame_count % 120 == 0:
                        logger.info(f"Frame {frame_count}: {tracked_count} tracked")

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

            # ✅ Chủ động loại bỏ trajectory đã hết hạn để tránh hiển thị "vệt ma"
            # Prune ngay với active_seconds (không giữ thêm 2x) để tránh ghost trajectories
            if trajectory_tracker:
                prune_window = max(settings.TRAJECTORY_ACTIVE_SECONDS, 1.0)  # Giảm từ 2x xuống 1x
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

            # Copy frame để tránh ghosting (vẽ trên frame mới mỗi lần)
            frame_display = frame.copy()

            # Vẽ detections - CHỈ vẽ detections TRONG ROI
            if detector and detections_to_draw:
                frame_display = detector.draw_detections(frame_display, detections_to_draw)
            update_vehicle_count(src, vehicle_count)
            if frame_count % 100 == 0 and detections:
                density_info = get_vehicle_density_info(vehicle_count)

            # ✅ Vẽ trajectory sau khi có track và detection
            # CHỈ VẼ trajectories có update gần đây (active) để tránh ghost
            if trajectory_tracker and trajectory_drawer:
                frame_display = trajectory_drawer.draw_all_trajectories(
                    frame_display,
                    trajectory_tracker,
                    active_only=True,  # CHỈ vẽ active trajectories
                    active_seconds=settings.TRAJECTORY_ACTIVE_SECONDS,  # 5 giây
                    stopline_y=stopline_y_pixels,
                    pixels_per_meter=settings.PIXELS_PER_METER,
                )

            # Vẽ thông tin vị trí và thời gian ở góc trái trên
            if location or camera_name:
                # Vị trí (dòng 1)
                text_location = location or camera_name or "Unknown"
                cv2.putText(
                    frame_display,
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
                    frame_display,
                    current_time,
                    (10, 60),  # Dòng 2, cách dòng 1 khoảng 30px
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA
                )

            # Validate frame một lần nữa sau detection
            if frame_display is None or frame_display.size == 0:
                logger.warning("Frame bị invalid sau detection, bỏ qua")
                continue

            # Encode frame thành JPEG với error handling tốt hơn
            encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)]

            try:
                ok, buffer = cv2.imencode(".jpg", frame_display, encode_params)

                if not ok or buffer is None:
                    logger.warning("Không thể encode frame, bỏ qua")
                    continue
            except Exception as e:
                logger.error(f"Lỗi khi encode frame: {e}")
                continue

            jpg_bytes: bytes = buffer.tobytes()

            # ✅ FPS THROTTLE: Chỉ YIELD frame khi đủ thời gian từ lần yield trước
            # - Detection đã xử lý NGAY → timestamp CHÍNH XÁC ✅
            # - Chỉ throttle YIELD để điều khiển tốc độ hiển thị (không ảnh hưởng tốc độ tính toán)
            # - Ví dụ: Camera 30 FPS, yield 10 FPS → Xử lý 30 frame/s nhưng chỉ hiển thị 10 frame/s
            current_time = time.time()

            # Lần đầu tiên hoặc đã đủ thời gian
            if last_yield_time == 0 or (current_time - last_yield_time) >= delay:
                yield (
                    boundary
                    + b"\r\nContent-Type: image/jpeg"
                    + b"\r\nContent-Length: " + str(len(jpg_bytes)).encode()
                    + b"\r\n\r\n"
                    + jpg_bytes
                    + b"\r\n"
                )
                last_yield_time = current_time
            # Nếu chưa đủ thời gian: Không yield, tiếp tục loop xử lý frame tiếp theo
            # (Frame này vẫn được detect → timestamp chính xác, chỉ không hiển thị)

    except GeneratorExit:
        pass
    except Exception as e:
        logger.error(f"Lỗi trong quá trình streaming: {e}")
    finally:
        try:
            cap.release()
        except Exception:
            pass
