"""
RTSP Streaming Service - MJPEG streaming từ RTSP/HTTP với YOLO detection

Chức năng:
- Mở và duy trì kết nối RTSP (với auto-reconnect)
- Generate MJPEG stream từ RTSP source
- Tích hợp YOLO detection real-time
"""

import os
import time
from typing import Generator, Optional
import cv2

from ..core.config import settings
from .detector import get_yolo_detector, filter_detections_by_roi
from .vehicle_density import count_vehicles, get_vehicle_density_info, update_vehicle_count
from ..utils.logger import stream_logger as logger


def open_capture(
    src: str,
    reconnect: bool = True,
    timeout_sec: Optional[int] = None
) -> Optional[cv2.VideoCapture]:
    """
    Mở VideoCapture cho nguồn RTSP/URL với cơ chế retry

    Args:
        src: URL của nguồn video (RTSP/HTTP)
        reconnect: Có thử kết nối lại không
        timeout_sec: Thời gian timeout (giây), mặc định lấy từ settings

    Returns:
        VideoCapture object hoặc None nếu thất bại
    """
    if timeout_sec is None:
        timeout_sec = settings.STREAM_RECONNECT_TIMEOUT

    start_time = time.time()

    while True:
        # Tạo VideoCapture với các options để handle errors tốt hơn
        # Sử dụng RTSP TCP transport để tránh packet loss
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

        cap = cv2.VideoCapture(src, cv2.CAP_FFMPEG)

        # Set các properties để skip corrupted frames và giảm latency
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer nhỏ để giảm latency
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)  # Timeout 5s
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)  # Read timeout 5s

        if cap.isOpened():
            return cap

        cap.release()

        # Kiểm tra timeout
        elapsed = time.time() - start_time
        if not reconnect or elapsed > timeout_sec:
            logger.error(f"✗ Không thể kết nối tới nguồn sau {elapsed:.1f}s: {src}")
            return None

        logger.warning(f"Đang thử kết nối lại... (đã {elapsed:.1f}s)")
        time.sleep(0.5)


def generate_mjpeg(
    src: str,
    fps: Optional[int] = None,
    jpeg_quality: Optional[int] = None,
    enable_detection: bool = True,
    roi: Optional[list] = None
) -> Generator[bytes, None, None]:
    """
    Generator tạo MJPEG stream từ nguồn RTSP/HTTP với YOLO detection

    Args:
        src: URL nguồn video
        fps: FPS mục tiêu, mặc định lấy từ settings
        jpeg_quality: Chất lượng JPEG (10-95), mặc định lấy từ settings
        enable_detection: Bật/tắt YOLO detection
        roi: ROI normalized [{x, y}, ...] để filter bbox (None = hiện tất cả)

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

                    # Đếm mật độ phương tiện TỪ TẤT CẢ DETECTIONS (trước khi filter)
                    vehicle_count = count_vehicles(detections)

                    # Filter detections theo ROI (chỉ vẽ bbox trong ROI)
                    h, w = frame.shape[:2]
                    detections_to_draw = filter_detections_by_roi(detections, roi, w, h)

                    # Vẽ chỉ detections trong ROI
                    frame = detector.draw_detections(frame, detections_to_draw)

                    # Cập nhật cache cho camera này
                    update_vehicle_count(src, vehicle_count)

                    # Update density cache
                    if frame_count % 100 == 0 and detections:
                        density_info = get_vehicle_density_info(vehicle_count)

                except Exception as e:
                    logger.error(f"Lỗi khi chạy detection: {e}")
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
