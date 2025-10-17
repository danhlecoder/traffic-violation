"""
Camera Management API

Endpoints:
- GET    /api/cameras         - Danh sách cameras
- POST   /api/cameras         - Thêm/cập nhật camera
- GET    /api/cameras/{id}    - Chi tiết camera
- PUT    /api/cameras/{id}/regions - Cập nhật regions
- DELETE /api/cameras/{id}    - Xóa camera
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException

from ..schemas.camera import Camera, CameraRegion
from ..services.database import get_db
from ..utils.logger import app_logger as logger


router = APIRouter()


@router.get('/api/cameras')
def list_cameras():
    """
    Lấy danh sách tất cả cameras với regions đã cấu hình

    Returns:
        List[Camera]: Danh sách cameras
    """
    try:
        db = get_db()
        items = list(db.cameras.find({}))

        # Chuẩn hóa dữ liệu
        for item in items:
            item['id'] = item.get('id') or str(item.get('_id'))
            item.pop('_id', None)

        logger.info(f"Trả về {len(items)} cameras")
        return items

    except Exception as e:
        logger.error(f"Lỗi khi lấy danh sách cameras: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")


@router.post('/api/cameras')
def upsert_camera(cam: Camera):
    """
    Thêm mới hoặc cập nhật camera

    Args:
        cam: Thông tin camera

    Returns:
        dict: Kết quả thành công
    """
    try:
        db = get_db()

        # Chuyển đổi sang dict, loại bỏ các field None để tránh ghi đè
        doc = (
            cam.model_dump(exclude_none=True)
            if hasattr(cam, 'model_dump')
            else cam.dict(exclude_none=True)
        )

        # Upsert camera
        db.cameras.update_one(
            {'id': cam.id},
            {'$set': doc},
            upsert=True
        )

        logger.info(f"✓ Đã lưu camera: {cam.id} - {cam.name}")
        return {'ok': True}

    except Exception as e:
        logger.error(f"Lỗi khi lưu camera {cam.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi lưu camera: {str(e)}")


@router.get('/api/cameras/{cam_id}')
def get_camera(cam_id: str):
    """
    Lấy thông tin chi tiết một camera

    Args:
        cam_id: ID của camera

    Returns:
        Camera: Thông tin camera
    """
    try:
        db = get_db()
        doc = db.cameras.find_one({'id': cam_id})

        if not doc:
            logger.warning(f"Không tìm thấy camera: {cam_id}")
            raise HTTPException(status_code=404, detail='Không tìm thấy camera')

        # Chuẩn hóa
        doc['id'] = doc.get('id') or str(doc.get('_id'))
        doc.pop('_id', None)

        logger.info(f"Trả về thông tin camera: {cam_id}")
        return doc

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi lấy camera {cam_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")


@router.put('/api/cameras/{cam_id}/regions')
def update_regions(cam_id: str, regions: CameraRegion):
    """
    Cập nhật regions (vạch dừng và ROI) cho camera

    Args:
        cam_id: ID của camera
        regions: Thông tin regions mới

    Returns:
        dict: Kết quả thành công
    """
    try:
        db = get_db()

        # Chuyển đổi sang dict
        payload = (
            regions.model_dump(exclude_unset=True, exclude_none=False)
            if hasattr(regions, 'model_dump')
            else regions.dict(exclude_unset=True, exclude_none=False)
        )

        if not payload:
            return {'ok': True}

        # Xây dựng update query
        to_set: Dict[str, Any] = {}
        to_unset: Dict[str, str] = {}

        for key, value in payload.items():
            path = f'regions.{key}'

            # Xử lý trường hợp xóa (null hoặc mảng rỗng)
            if value is None:
                to_unset[path] = ""
                continue

            if key == 'roi' and isinstance(value, list) and len(value) == 0:
                to_unset[path] = ""
                continue

            # Set giá trị mới
            to_set[path] = value

        # Tạo update document
        update_doc: Dict[str, Any] = {}
        if to_set:
            update_doc['$set'] = to_set
        if to_unset:
            update_doc['$unset'] = to_unset

        if not update_doc:
            return {'ok': True}

        # Thực hiện update
        result = db.cameras.update_one(
            {'id': cam_id},
            update_doc,
            upsert=True
        )

        logger.info(f"✓ Đã cập nhật regions cho camera: {cam_id}")
        return {'ok': True}

    except Exception as e:
        logger.error(f"Lỗi khi cập nhật regions cho camera {cam_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi cập nhật: {str(e)}")


@router.delete('/api/cameras/{cam_id}')
def delete_camera(cam_id: str):
    """
    Xóa camera

    Args:
        cam_id: ID của camera

    Returns:
        dict: Kết quả thành công
    """
    try:
        db = get_db()
        result = db.cameras.delete_one({'id': cam_id})

        if result.deleted_count == 0:
            logger.warning(f"Không tìm thấy camera để xóa: {cam_id}")
            raise HTTPException(status_code=404, detail='Không tìm thấy camera')

        logger.info(f"✓ Đã xóa camera: {cam_id}")
        return {'ok': True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi xóa camera {cam_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi xóa: {str(e)}")
