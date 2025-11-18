"""
Vehicle Density Service - Đếm và phân loại mật độ phương tiện
"""

from typing import List, Dict, Any
from threading import Lock

from ...config.config import settings
from ..constants import VEHICLE_CLASSES


def count_vehicles(detections: List[Dict[str, Any]]) -> int:
    """
    Đếm số lượng phương tiện trong danh sách detections

    Args:
        detections: List các detection từ YOLO detector
                   Format: [{"bbox": [...], "confidence": ..., "class_name": ...}, ...]

    Returns:
        Số lượng phương tiện
    """
    if not detections:
        return 0

    count = sum(1 for det in detections if det.get("class_name") in VEHICLE_CLASSES)
    return count


def get_vehicle_density_info(vehicle_count: int) -> Dict[str, Any]:
    """
    Phân loại mật độ dựa trên số lượng phương tiện

    Ngưỡng (khớp với frontend):
    - 0: Vắng
    - 1-5: Thưa
    - 6-15: Đông
    - >15: Rất đông

    Args:
        vehicle_count: Số lượng phương tiện

    Returns:
        {"count": int, "level": str, "description": str}
    """
    if vehicle_count == 0:
        level, description = "empty", "Vắng"
    elif vehicle_count <= settings.DENSITY_THRESHOLD_LOW:
        level, description = "low", "Thưa"
    elif vehicle_count <= settings.DENSITY_THRESHOLD_MEDIUM:
        level, description = "medium", "Đông"
    else:
        level, description = "high", "Rất đông"

    return {"count": vehicle_count, "level": level, "description": description}


def get_vehicles_by_type(detections: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Đếm số lượng từng loại phương tiện

    Args:
        detections: List các detection từ YOLO detector

    Returns:
        {"car": int, "motorcycle": int, "bus": int, "truck": int}
    """
    result = {"car": 0, "motorcycle": 0, "bus": 0, "truck": 0}

    if not detections:
        return result

    for det in detections:
        class_name = det.get("class_name")
        if class_name in result:
            result[class_name] += 1

    return result


# Cache management (thread-safe)
_vehicle_count_cache: Dict[str, int] = {}
_cache_lock = Lock()


def update_vehicle_count(camera_url: str, count: int) -> None:
    """
    Cập nhật số lượng phương tiện cho camera (thread-safe)

    Args:
        camera_url: URL của camera (RTSP)
        count: Số lượng phương tiện hiện tại
    """
    with _cache_lock:
        _vehicle_count_cache[camera_url] = count


def get_vehicle_count(camera_url: str) -> int:
    """
    Lấy số lượng phương tiện của camera từ cache

    Args:
        camera_url: URL của camera (RTSP)

    Returns:
        Số lượng phương tiện, mặc định 0 nếu chưa có
    """
    with _cache_lock:
        return _vehicle_count_cache.get(camera_url, 0)


def clear_vehicle_cache() -> None:
    """Xóa toàn bộ cache vehicle count"""
    with _cache_lock:
        _vehicle_count_cache.clear()
