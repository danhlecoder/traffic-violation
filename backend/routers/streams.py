from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..src.rtsp_stream.streamer import generate_mjpeg
from ..src.utils.detec_line import detect_stop_line_normalized, center_crop_to_16_9
from ..src.utils.logger import app_logger as log
import base64
import numpy as np
import cv2


router = APIRouter()


@router.get("/api/stream")
def stream(
    rtsp: Optional[str] = Query(None, alias="src"),
    fps: int = Query(30, ge=1, le=60),
    quality: int = Query(80, ge=10, le=95),
):
    """
    MJPEG stream from RTSP/HTTP video source.

    Usage (frontend <img>):
      <img src="http://localhost:8000/api/stream?src=ENCODED_RTSP_URL" />
    """
    if not rtsp:
        raise HTTPException(status_code=400, detail="Missing 'src' query (RTSP/URL)")

    generator = generate_mjpeg(rtsp, fps=fps, jpeg_quality=quality)
    return StreamingResponse(generator, media_type="multipart/x-mixed-replace; boundary=frame")


## Snapshot endpoint đã loại bỏ theo yêu cầu


class DetectImagePayload(BaseModel):
    image: str  # data URL hoặc base64 ảnh JPEG/PNG


@router.post("/api/detect/stopline")
def detect_stopline_from_image(payload: DetectImagePayload):
    """
    Nhận ảnh (data URL hoặc base64) từ frontend và chạy phát hiện vạch dừng.
    Trả về 2 điểm đã chuẩn hóa [0..1] nếu tìm thấy.
    """
    data = payload.image.strip()
    # Hỗ trợ data URL: data:image/jpeg;base64,....
    if data.startswith("data:"):
        try:
            data = data.split(",", 1)[1]
        except Exception:
            raise HTTPException(status_code=400, detail="Data URL không hợp lệ")

    try:
        jpg_bytes = base64.b64decode(data, validate=False)
    except Exception:
        raise HTTPException(status_code=400, detail="Base64 ảnh không hợp lệ")

    buf = np.frombuffer(jpg_bytes, dtype=np.uint8)
    frame = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Không giải mã được ảnh")

    # Đồng bộ với luồng snapshot/detect: crop 16:9 và resize chuẩn
    frame = center_crop_to_16_9(frame)
    try:
        frame = cv2.resize(frame, (1280, 720), interpolation=cv2.INTER_AREA)
    except Exception:
        pass

    # Downscale cho nhánh detect để tăng tốc
    det_in = frame
    try:
        det_in = cv2.resize(frame, (960, 540), interpolation=cv2.INTER_AREA)
    except Exception:
        det_in = frame

    try:
        result = detect_stop_line_normalized(det_in)
    except Exception:
        try:
            log.exception("Lỗi phát hiện vạch dừng từ ảnh")
        except Exception:
            pass
        result = None

    payload_out = {"stopLine": None}
    if result:
        (x1, y1), (x2, y2) = result
        payload_out["stopLine"] = [
            {"x": float(x1), "y": float(y1)},
            {"x": float(x2), "y": float(y2)},
        ]
    return payload_out

