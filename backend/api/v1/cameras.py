"""
Camera Management API - CRUD operations cho cameras
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException

from ...utils.camera import Camera, CameraRegion
from ...config.config import settings
from ..clients.mongodb_service import get_mongodb_service
from ...utils.logger import app_logger as logger


router = APIRouter()


@router.get('/cameras')
def list_cameras():
    """
    Lấy danh sách tất cả cameras
    """
    try:
        service = get_mongodb_service()
        items = service.get_cameras()
        logger.info(f"Trả về {len(items)} cameras")
        return items

    except Exception as e:
        logger.error(f"Lỗi khi lấy danh sách cameras: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")


@router.post('/cameras')
def upsert_camera(cam: Camera):
    """
    Tạo hoặc cập nhật camera
    """
    try:
        logger.info(f"📥 Received camera data: {cam.model_dump()}")
        service = get_mongodb_service()

        doc = cam.model_dump(exclude_none=True) if hasattr(cam, 'model_dump') else cam.dict(exclude_none=True)
        success = service.create_or_update_camera(doc)

        if success:
            logger.info(f"✓ Đã lưu camera: {cam.id} - {cam.name}")
            return {'ok': True, 'id': cam.id}
        else:
            raise HTTPException(status_code=500, detail="Failed to save camera")

    except Exception as e:
        logger.error(f"Lỗi khi lưu camera {cam.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi lưu camera: {str(e)}")


@router.get('/cameras/{cam_id}')
def get_camera(cam_id: str):
    """
    Lấy chi tiết một camera theo ID
    """
    try:
        service = get_mongodb_service()
        doc = service.get_camera(cam_id)

        # Bổ sung lineB nếu chưa có mà đã có stopLine (tính tương đối theo chiều cao 1080)
        try:
            regions = (doc or {}).get("regions") if doc else None
            if regions and regions.get("stopLine") and not regions.get("lineB"):
                stop = regions["stopLine"]
                if isinstance(stop, list) and len(stop) == 2:
                    base_h = 1080.0  # giả định chiều cao chuẩn để quy đổi px→tương đối
                    dy_rel = max(0.0, float(settings.TRAJECTORY_PIXELS_BETWEEN_LINES) / base_h)
                    p1 = {"x": float(stop[0]["x"]), "y": max(0.0, float(stop[0]["y"]) - dy_rel)}
                    p2 = {"x": float(stop[1]["x"]), "y": max(0.0, float(stop[1]["y"]) - dy_rel)}
                    regions["lineB"] = [p1, p2]
                    doc["regions"] = regions
        except Exception:
            pass

        if not doc:
            logger.warning(f"Không tìm thấy camera: {cam_id}")
            raise HTTPException(status_code=404, detail='Không tìm thấy camera')

        logger.info(f"Trả về thông tin camera: {cam_id}")
        return doc

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi lấy camera {cam_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")


@router.put('/cameras/{cam_id}/regions')
def update_regions(cam_id: str, regions: CameraRegion):
    """
    Cập nhật ROI/stopline cho camera
    """
    try:
        logger.info(f"📦 Update regions for camera {cam_id}")
        service = get_mongodb_service()

        # Convert regions to dict
        regions_dict = regions.model_dump() if hasattr(regions, 'model_dump') else regions.dict()

        # Tự động sinh lineB nếu chỉ gửi stopLine
        try:
            stop = regions_dict.get("stopLine")
            lineb = regions_dict.get("lineB")
            if stop and not lineb and isinstance(stop, list) and len(stop) == 2:
                base_h = 1080.0  # giả định chiều cao chuẩn để quy đổi px→tương đối
                dy_rel = max(0.0, float(settings.TRAJECTORY_PIXELS_BETWEEN_LINES) / base_h)
                p1 = {"x": float(stop[0]["x"]), "y": max(0.0, float(stop[0]["y"]) - dy_rel)}
                p2 = {"x": float(stop[1]["x"]), "y": max(0.0, float(stop[1]["y"]) - dy_rel)}
                regions_dict["lineB"] = [p1, p2]
        except Exception:
            pass

        success = service.update_camera_regions(cam_id, regions_dict)

        if success:
            logger.info(f"✓ Đã cập nhật regions cho camera: {cam_id}")
            return {'ok': True, 'message': 'Regions updated successfully'}
        else:
            raise HTTPException(status_code=404, detail='Camera not found')

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi update regions {cam_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")


@router.put('/cameras/{cam_id}/detection-rules')
def update_detection_rules(cam_id: str, rules: Dict[str, Any]):
    """
    Cập nhật detection rules cho camera
    """
    try:
        logger.info(f"📦 Update detection rules for camera {cam_id}")
        service = get_mongodb_service()

        success = service.update_camera_detection_rules(cam_id, rules)

        if success:
            logger.info(f"✓ Đã cập nhật detection rules cho camera: {cam_id}")
            return {'ok': True, 'message': 'Detection rules updated successfully'}
        else:
            raise HTTPException(status_code=404, detail='Camera not found')

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi update detection rules {cam_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")


@router.delete('/cameras/{cam_id}')
def delete_camera(cam_id: str):
    """
    Xóa camera theo ID
    """
    try:
        logger.info(f"🗑️  Delete camera: {cam_id}")
        service = get_mongodb_service()

        success = service.delete_camera(cam_id)

        if success:
            logger.info(f"✓ Đã xóa camera: {cam_id}")
            return {'ok': True, 'message': 'Camera deleted successfully'}
        else:
            raise HTTPException(status_code=404, detail='Camera not found')

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi xóa camera {cam_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")
