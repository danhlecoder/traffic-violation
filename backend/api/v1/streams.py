"""
Streaming API - MJPEG streaming từ RTSP/HTTP với YOLO detection
"""

from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse

from ...core.streaming.mjpeg import generate_mjpeg
from ...clients.mongodb_service import get_mongodb_service
from ...utils.logger import app_logger as logger
from ...core.analysis.density import get_vehicle_density_info, get_vehicle_count


router = APIRouter()


@router.get("/stream")
def stream(
    rtsp: Optional[str] = Query(None, alias="src", description="URL nguồn RTSP/HTTP"),
    fps: Optional[int] = Query(None, ge=1, le=60, description="FPS mục tiêu (None = dùng settings)"),
    quality: Optional[int] = Query(None, ge=10, le=95, description="Chất lượng JPEG (None = dùng settings)"),
    detection: bool = Query(True, description="Bật/tắt YOLO detection")
):
    """
    Endpoint trả về MJPEG stream từ RTSP/HTTP source
    
    Headers để tránh timeout:
    - Connection: keep-alive
    - Keep-Alive: timeout=300
    
    MJPEG stream từ nguồn RTSP/HTTP với YOLO detection (via API)
    """
    if not rtsp:
        logger.warning("Thiếu tham số 'src' (RTSP URL)")
        raise HTTPException(
            status_code=400,
            detail="Thiếu tham số 'src' (URL RTSP/HTTP)"
        )

    try:
        logger.info(f"Bắt đầu stream từ: {rtsp} (FPS={fps}, Quality={quality}, Detection={detection})")

        # Lấy camera info từ MongoDB API
        roi = None
        stopline = None
        camera_id = None
        camera_name = None
        location = None
        try:
            service = get_mongodb_service()
            cameras = service.get_cameras()
            
            # Find camera by RTSP URL
            camera_doc = None
            for cam in cameras:
                if cam.get('rtsp') == rtsp:
                    camera_doc = cam
                    break
            
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
                        logger.warning(f"⚠️  Camera {camera_id} KHÔNG có ROI - sẽ track TOÀN BỘ khung hình")

                    # Load stopline
                    if regions.get('stopLine'):
                        raw_stopline = regions['stopLine']

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
                        logger.info(f"⚠️  Camera {camera_id} KHÔNG có stopLine - chỉ detect ROI entry violations")
                else:
                    logger.warning(f"⚠️  Camera {camera_id} KHÔNG có regions config - sẽ track TOÀN BỘ và không detect stopline")
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
            media_type="multipart/x-mixed-replace; boundary=frame",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Connection": "keep-alive",
                "Keep-Alive": "timeout=300, max=1000",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )

    except Exception as e:
        logger.error(f"Lỗi khi tạo stream: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Không thể stream: {str(e)}"
        )


@router.get("/stream/density")
def get_stream_density(src: str = Query(..., description="URL nguồn RTSP/HTTP")):
    """
    Lấy mật độ phương tiện hiện tại của stream
    
    Returns:
        {
            "count": 5,
            "level": "low" | "medium" | "high",
            "description": "Thưa"
        }
    """
    try:
        vehicle_count = get_vehicle_count(src)
        return get_vehicle_density_info(vehicle_count)
    except Exception as e:
        logger.error(f"Lỗi lấy density: {e}")
        raise HTTPException(status_code=500, detail=str(e))
