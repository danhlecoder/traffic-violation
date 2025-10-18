"""
Streaming API - MJPEG streaming từ RTSP/HTTP với YOLO detection
"""

from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse

from ..services.streaming import generate_mjpeg
from ..services.database import get_db
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

        # Lấy ROI từ database (nếu có)
        roi = None
        try:
            db = get_db()
            camera_doc = db.cameras.find_one({'rtsp': rtsp})
            if camera_doc and camera_doc.get('regions') and camera_doc['regions'].get('roi'):
                roi = camera_doc['regions']['roi']
                logger.info(f"Đã load ROI cho camera (RTSP: {rtsp}): {len(roi)} điểm")
        except Exception as e:
            logger.warning(f"Không thể load ROI từ DB: {e}")

        generator = generate_mjpeg(
            src=rtsp,
            fps=fps,
            jpeg_quality=quality,
            enable_detection=detection,
            roi=roi
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
