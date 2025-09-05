import time
from typing import Generator, Optional

import cv2


def open_capture(src: str, reconnect: bool = True, timeout_sec: int = 5) -> Optional[cv2.VideoCapture]:
    """Open a VideoCapture for an RTSP/URL source with basic retry."""
    start = time.time()
    cap: Optional[cv2.VideoCapture] = None
    while True:
        cap = cv2.VideoCapture(src)
        if cap.isOpened():
            return cap
        cap.release()
        if not reconnect or (time.time() - start) > timeout_sec:
            return None
        time.sleep(0.5)


def generate_mjpeg(src: str, fps: int = 30, jpeg_quality: int = 80) -> Generator[bytes, None, None]:
    """
    Generator that yields multipart MJPEG bytes from an RTSP/HTTP video source.

    This opens the source per-request and streams frames as JPEG images with the
    proper multipart boundaries, which can be consumed directly by <img> tags.
    """
    boundary = b"--frame"
    delay = 1.0 / max(1, fps)

    cap = open_capture(src)
    if cap is None:
        # Yield a single empty payload to let client handle error gracefully
        yield boundary + b"\r\nContent-Type: image/jpeg\r\n\r\n" + b"" + b"\r\n"
        return

    try:
        last_time = 0.0
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                # Try to reconnect once
                cap.release()
                cap = open_capture(src)
                if cap is None:
                    break
                continue

            # Throttle to target FPS
            now = time.time()
            if now - last_time < delay:
                time.sleep(max(0, delay - (now - last_time)))
            last_time = time.time()

            # Encode frame to JPEG
            ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)])
            if not ok:
                continue
            jpg: bytes = buf.tobytes()

            # Yield as multipart chunk
            yield (
                boundary
                + b"\r\nContent-Type: image/jpeg\r\nContent-Length: "
                + str(len(jpg)).encode()
                + b"\r\n\r\n"
                + jpg
                + b"\r\n"
            )
    finally:
        try:
            cap.release()
        except Exception:
            pass
