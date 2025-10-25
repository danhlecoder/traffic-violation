"""
Streaming API - MJPEG streaming từ RTSP/HTTP với YOLO detection
"""

from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse

from ..core.streaming.mjpeg import generate_mjpeg
from ..utils.database import get_db
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
    """
    if not rtsp:
        logger.warning("Thiếu tham số 'src' (RTSP URL)")
        raise HTTPException(
            status_code=400,
            detail="Thiếu tham số 'src' (URL RTSP/HTTP)"
        )

    try:
        logger.info(f"Bắt đầu stream từ: {rtsp} (FPS={fps}, Quality={quality}, Detection={detection})")

        # Lấy ROI, stopline và camera info từ database
        roi = None
        stopline = None
        camera_id = None
        camera_name = None
        location = None
        try:
            db = get_db()
            camera_doc = db.cameras.find_one({'rtsp': rtsp})
            if camera_doc:
                logger.info(f"✓ Tìm thấy camera trong DB cho rtsp: {rtsp}")
                camera_id = camera_doc.get('id')
                camera_name = camera_doc.get('name')
                location = camera_doc.get('location')

                if camera_doc.get('regions'):
                    regions = camera_doc['regions']

                    # Load ROI
                    if regions.get('roi'):
                        roi = regions['roi']
                        logger.info(f"✓ Đã load ROI cho camera {camera_id}: {len(roi)} điểm")
                    else:
                        logger.warning(f"✗ Camera {camera_id} KHÔNG có ROI trong DB!")

                    # Load stopline - Format từ frontend: [{"x": 0, "y": 0.66}, {"x": 1, "y": 0.66}]
                    if regions.get('stopLine'):
                        raw_stopline = regions['stopLine']

                        # stopLine là list của 2 points → lấy y từ point đầu
                        if isinstance(raw_stopline, list) and len(raw_stopline) > 0:
                            first_point = raw_stopline[0]
                            if isinstance(first_point, dict) and "y" in first_point:
                                y_value = float(first_point["y"])
                                stopline = {
                                    "y": y_value,
                                    "is_normalized": (0 <= y_value <= 1)
                                }
                                logger.info(f"✓ Đã load stopline: y={y_value:.3f}, normalized={stopline['is_normalized']}")
                            else:
                                logger.error(f"Stopline point format sai: {first_point}")

                        # Fallback: dict format
                        elif isinstance(raw_stopline, dict) and "y" in raw_stopline:
                            y_value = float(raw_stopline["y"])
                            stopline = {
                                "y": y_value,
                                "is_normalized": (0 <= y_value <= 1)
                            }
                            logger.info(f"✓ Đã load stopline (dict): y={y_value:.3f}")

                        else:
                            logger.error(f"Stopline format không đúng: {type(raw_stopline)}, value={raw_stopline}")
                    else:
                        logger.warning(f"Camera {camera_id} KHÔNG có stopLine config!")
            else:
                logger.warning(f"✗ KHÔNG tìm thấy camera trong DB cho rtsp: {rtsp}")
        except Exception as e:
            logger.warning(f"Không thể load camera info từ DB: {e}")

        generator = generate_mjpeg(
            src=rtsp,
            fps=fps,
            jpeg_quality=quality,
            enable_detection=detection,
            roi=roi,
            stopline=stopline,
            camera_id=camera_id,
            camera_name=camera_name,
            location=location,
            enable_violation_detection=True
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
