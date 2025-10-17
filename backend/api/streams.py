"""
Streaming & Detection API

Endpoints:
- GET  /api/stream          - MJPEG stream với YOLO detection
- POST /api/detect/stopline - Phát hiện vạch dừng từ ảnh
"""

from typing import Optional
import base64
import numpy as np
import cv2

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..services.streaming import generate_mjpeg
from ..services.detect_line import detect_stop_line_normalized, center_crop_to_16_9
from ..utils.logger import app_logger as logger


router = APIRouter()


@router.get("/api/stream")
def stream(
    rtsp: Optional[str] = Query(None, alias="src", description="URL nguồn RTSP/HTTP"),
    fps: int = Query(30, ge=1, le=60, description="FPS mục tiêu"),
    quality: int = Query(80, ge=10, le=95, description="Chất lượng JPEG"),
    detection: bool = Query(True, description="Bật/tắt YOLO detection")
):
    """
    MJPEG stream từ nguồn RTSP/HTTP với YOLO detection

    Args:
        rtsp: URL nguồn video (RTSP hoặc HTTP)
        fps: Frame per second mục tiêu (1-60)
        quality: Chất lượng JPEG (10-95)
        detection: Bật/tắt YOLO detection (mặc định: True)

    Returns:
        StreamingResponse: MJPEG stream

    Example:
        GET /api/stream?src=rtsp://example.com/stream&fps=30&quality=80&detection=true
    """
    if not rtsp:
        logger.warning("Thiếu tham số 'src' (RTSP URL)")
        raise HTTPException(
            status_code=400,
            detail="Thiếu tham số 'src' (URL RTSP/HTTP)"
        )

    try:
        logger.info(f"Bắt đầu stream từ: {rtsp} (FPS={fps}, Quality={quality}, Detection={detection})")

        generator = generate_mjpeg(
            src=rtsp,
            fps=fps,
            jpeg_quality=quality,
            enable_detection=detection
        )

        return StreamingResponse(
            generator,
            media_type="multipart/x-mixed-replace; boundary=frame"
        )

    except Exception as e:
        logger.error(f"Lỗi khi tạo stream: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi tạo stream: {str(e)}"
        )


class DetectImagePayload(BaseModel):
    """Schema cho request detect stopline từ ảnh"""
    image: str  # Base64 hoặc Data URL


@router.post("/api/detect/stopline")
def detect_stopline_from_image(payload: DetectImagePayload):
    """
    Phát hiện vạch dừng từ ảnh base64

    Args:
        payload: Ảnh dạng base64 hoặc data URL

    Returns:
        dict: Kết quả phát hiện với tọa độ chuẩn hóa [0..1]

    Example:
        POST /api/detect/stopline
        {
            "image": "data:image/jpeg;base64,/9j/4AAQ..."
        }
    """
    try:
        # Parse base64 image
        data = payload.image.strip()

        # Xử lý data URL
        if data.startswith("data:"):
            try:
                data = data.split(",", 1)[1]
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="Data URL không hợp lệ"
                )

        # Decode base64
        try:
            jpg_bytes = base64.b64decode(data, validate=False)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Base64 không hợp lệ"
            )

        # Decode image
        buffer = np.frombuffer(jpg_bytes, dtype=np.uint8)
        frame = cv2.imdecode(buffer, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(
                status_code=400,
                detail="Không thể giải mã ảnh"
            )

        # Xử lý ảnh: crop 16:9 và resize
        frame = center_crop_to_16_9(frame)

        try:
            frame = cv2.resize(frame, (1280, 720), interpolation=cv2.INTER_AREA)
        except Exception:
            pass

        # Downscale cho detection (tăng tốc độ)
        det_frame = frame
        try:
            det_frame = cv2.resize(frame, (960, 540), interpolation=cv2.INTER_AREA)
        except Exception:
            det_frame = frame

        # Chạy detection
        try:
            result = detect_stop_line_normalized(det_frame)
        except Exception as e:
            logger.exception(f"Lỗi khi phát hiện vạch dừng: {e}")
            result = None

        # Trả về kết quả
        response = {"stopLine": None}

        if result:
            (x1, y1), (x2, y2) = result
            response["stopLine"] = [
                {"x": float(x1), "y": float(y1)},
                {"x": float(x2), "y": float(y2)},
            ]
            logger.info(f"✓ Phát hiện vạch dừng: {response['stopLine']}")
        else:
            logger.info("Không phát hiện được vạch dừng")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi xử lý detect stopline: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi server: {str(e)}"
        )
