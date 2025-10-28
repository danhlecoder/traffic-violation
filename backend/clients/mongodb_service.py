"""
MongoDB API Service - Gọi MongoDB Service Qua HTTP
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from ..config.config import settings
from ..utils.logger import app_logger as logger
from .base_service import BaseAPIService


class MongoDBService(BaseAPIService):
    """Service để gọi MongoDB API"""
    
    def __init__(self):
        super().__init__(
            base_url=settings.MONGO_API_URL,
            timeout=10,
            service_name="MongoDB"
        )
    
    def _convert_datetime_to_str(self, data: Any) -> Any:
        """Chuyển đổi datetime objects sang ISO format strings đệ quy"""
        if isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, dict):
            return {k: self._convert_datetime_to_str(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_datetime_to_str(item) for item in data]
        return data
    
    # ========== CAMERAS ==========
    
    def get_cameras(self) -> List[Dict]:
        """Lấy danh sách tất cả cameras"""
        result = self._get("/v1/cameras")
        return result.get("cameras", []) if result else []
    
    def get_camera(self, camera_id: str) -> Optional[Dict]:
        """Lấy camera theo ID"""
        result = self._get(f"/v1/cameras/{camera_id}")
        return result.get("camera") if result else None
    
    def create_camera(self, camera_data: Dict) -> Optional[str]:
        """Tạo camera mới"""
        result = self._post("/v1/cameras", camera_data)
        if result:
            logger.info(f"✓ Đã tạo camera: {result.get('id')}")
            return result.get("id")
        return None
    
    def delete_camera(self, camera_id: str) -> bool:
        """Xóa camera theo ID"""
        success = self._delete(f"/v1/cameras/{camera_id}")
        if success:
            logger.info(f"✓ Đã xóa camera: {camera_id}")
        return success
    
    def update_camera_regions(self, camera_id: str, regions: Dict) -> bool:
        """Cập nhật regions cho camera (ROI, stopLine)"""
        success = self._put(f"/v1/cameras/{camera_id}/regions", regions)
        if success:
            logger.info(f"✓ Đã cập nhật regions cho camera: {camera_id}")
        return success
    
    # ========== VIOLATIONS ==========
    
    def get_violations(self, status: str = None, camera_id: str = None, limit: int = 100, offset: int = 0) -> Dict:
        """Lấy danh sách vi phạm với bộ lọc"""
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if camera_id:
            params["camera_id"] = camera_id
        
        result = self._get("/v1/violations", params=params)
        return result if result else {"data": [], "total": 0}
    
    def create_violation(self, violation_data: Dict) -> Optional[str]:
        """Tạo vi phạm mới"""
        # Chuyển datetime objects sang ISO strings
        clean_data = self._convert_datetime_to_str(violation_data)
        
        result = self._post("/v1/violations", clean_data)
        return result.get("id") if result else None


# Singleton
_mongodb_service = None

def get_mongodb_service() -> MongoDBService:
    """Lấy MongoDB service instance"""
    global _mongodb_service
    if _mongodb_service is None:
        _mongodb_service = MongoDBService()
    return _mongodb_service
