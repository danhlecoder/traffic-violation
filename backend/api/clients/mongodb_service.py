"""
MongoDB API Service - Gọi MongoDB Service Qua HTTP
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from ...config.config import settings
from ...utils.logger import app_logger as logger
from .base_service import BaseAPIService


class MongoDBService(BaseAPIService):
    """Service để gọi MongoDB API"""

    def __init__(self):
        super().__init__(
            base_url=settings.MONGO_API_URL,
            timeout=10,
            service_name="MongoDB"
        )
        self._camera_cache: Dict[str, Tuple[float, Optional[Dict[str, Any]]]] = {}
        self._camera_cache_ttl = float(settings.MONGO_CAMERA_CACHE_TTL or 0.0)

    def get_cameras(self) -> List[Dict[str, Any]]:
        """Lấy danh sách tất cả cameras"""
        result = self._get("/v1/cameras")
        return result.get("cameras", []) if result else []

    def get_camera(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin một camera"""
        if self._camera_cache_ttl > 0:
            cached = self._camera_cache.get(camera_id)
            if cached:
                expires_at, data = cached
                if expires_at > time.monotonic():
                    return data
                self._camera_cache.pop(camera_id, None)

        result = self._get(f"/v1/cameras/{camera_id}")
        camera = result.get("camera") if result else None

        if self._camera_cache_ttl > 0:
            expires_at = time.monotonic() + self._camera_cache_ttl
            self._camera_cache[camera_id] = (expires_at, camera)

        return camera

    def create_or_update_camera(self, camera_data: Dict[str, Any]) -> bool:
        """Tạo hoặc cập nhật camera"""
        result = self._post("/v1/cameras", camera_data)
        success = result is not None and result.get("success", False)
        if success:
            self._invalidate_camera_cache()
        return success

    def update_camera_regions(self, camera_id: str, regions: Dict[str, Any]) -> bool:
        """Cập nhật regions (ROI, stopline) cho camera"""
        updated = self._put(f"/v1/cameras/{camera_id}/regions", regions)
        if updated:
            self._invalidate_camera_cache(camera_id)
        return bool(updated)

    def update_camera_detection_rules(self, camera_id: str, rules: Dict[str, Any]) -> bool:
        """Cập nhật detection rules cho camera"""
        result = self._put(f"/v1/cameras/{camera_id}/detection-rules", rules)
        success = result is not None and result.get("success", False)
        if success:
            self._invalidate_camera_cache(camera_id)
        return success

    def delete_camera(self, camera_id: str) -> bool:
        """Xóa camera"""
        deleted = self._delete(f"/v1/cameras/{camera_id}")
        if deleted:
            self._invalidate_camera_cache(camera_id)
        return deleted

    def save_violation(self, violation: Dict[str, Any]) -> Optional[str]:
        """Lưu violation"""
        result = self._post("/v1/violations", violation)
        return result.get("id") if result else None

    def get_violations(
        self,
        camera_id: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 10000,  # Tăng limit mặc định để lấy toàn bộ
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Lấy danh sách violations với filter"""
        params = {"limit": limit, "offset": offset}

        if camera_id:
            params["camera_id"] = camera_id
        if status:
            params["status"] = status
        if start_time:
            params["start_time"] = start_time.isoformat()
        if end_time:
            params["end_time"] = end_time.isoformat()

        result = self._get("/v1/violations", params=params)
        return result.get("data", []) if result else []

    def update_violation(self, track_id: str, update_data: Dict[str, Any]) -> bool:
        """Cập nhật violation theo track_id"""
        result = self._put(f"/v1/violations/{track_id}", update_data)
        return result is not None and result.get("success", False)

    def get_violation(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Lấy violation theo track_id"""
        result = self._get(f"/v1/violations/{track_id}")
        return result.get("violation") if result else None

    def _invalidate_camera_cache(self, camera_id: Optional[str] = None) -> None:
        """Xóa cache camera theo ID hoặc toàn bộ"""
        if camera_id:
            self._camera_cache.pop(camera_id, None)
        else:
            self._camera_cache.clear()


# Singleton
_mongodb_service = None

def get_mongodb_service() -> MongoDBService:
    """Lấy MongoDB service instance"""
    global _mongodb_service
    if _mongodb_service is None:
        _mongodb_service = MongoDBService()
    return _mongodb_service
