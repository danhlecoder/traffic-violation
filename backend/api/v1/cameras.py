"""
Camera Management API - CRUD operations cho cameras
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException

from ...utils.camera import Camera, CameraRegion
from ...clients.mongodb_service import get_mongodb_service
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
        camera_id = service.create_camera(doc)
        
        if camera_id:
            logger.info(f"✓ Đã lưu camera: {cam.id} - {cam.name}")
            return {'ok': True, 'id': camera_id}
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
