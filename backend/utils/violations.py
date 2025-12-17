"""
Utilities Violation - Hàm hỗ trợ dùng chung cho các bộ xử lý vi phạm
"""

import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..config.config import settings
from .logger import app_logger as logger
from ..core.constants import VEHICLE_CLASSES
from ..api.clients.mongodb_service import get_mongodb_service


_CAMERA_CONF_CACHE: Dict[str, Tuple[float, Optional[float]]] = {}
_CAMERA_CONF_CACHE_TTL = float(settings.MONGO_CAMERA_CACHE_TTL or 0.0)


def _get_camera_min_confidence(camera_id: str) -> Optional[float]:
    """Lấy minConfidence từ detection_rules của camera với cache TTL."""
    if not camera_id:
        return None

    if _CAMERA_CONF_CACHE_TTL > 0:
        cached = _CAMERA_CONF_CACHE.get(camera_id)
        if cached:
            expires_at, value = cached
            if expires_at > time.monotonic():
                return value
            _CAMERA_CONF_CACHE.pop(camera_id, None)

    try:
        camera = get_mongodb_service().get_camera(camera_id)
        rules = camera.get("detection_rules") if camera else None
        min_conf = rules.get("minConfidence") if rules else None
        value = float(min_conf) if min_conf is not None else None
    except Exception as error:
        logger.debug(f"Không lấy được detection_rules từ camera {camera_id}: {error}")
        return None

    if _CAMERA_CONF_CACHE_TTL > 0:
        _CAMERA_CONF_CACHE[camera_id] = (time.monotonic() + _CAMERA_CONF_CACHE_TTL, value)

    return value


def normalize_stopline_y(stopline: Dict[str, Any], frame_height: int) -> Optional[float]:
    """
    Chuyển stopline sang toạ độ pixel tuyệt đối (nếu cần).
    """
    if not stopline or "y" not in stopline:
        return None

    try:
        stopline_y_raw = float(stopline["y"])
    except (TypeError, ValueError):
        logger.error("Stopline 'y' không hợp lệ")
        return None

    if stopline.get("is_normalized", False):
        return stopline_y_raw * frame_height
    return stopline_y_raw

# TODO: Tìm biển số trong frame chính
def find_plate_detection_for_vehicle(
    vehicle_det: Dict[str, Any],
    detections: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Tìm detection biển số nằm trong bbox của phương tiện.
    """
    vx1, vy1, vx2, vy2 = vehicle_det.get("bbox", [0, 0, 0, 0])
    plates = [det for det in detections if det.get("class_name") == "license_plate"]
    for plate in plates:
        bbox = plate.get("bbox")
        if not bbox or len(bbox) != 4:
            continue
        px1, py1, px2, py2 = bbox
        pcx, pcy = (px1 + px2) / 2, (py1 + py2) / 2
        if vx1 <= pcx <= vx2 and vy1 <= pcy <= vy2:
            return plate
    return None


# TODO: Tiềm biển số Detect trên vehicle crop
def detect_plate_on_vehicle_crop(
    detector,
    frame: np.ndarray,
    vehicle_det: Dict[str, Any],
    camera_id: Optional[str] = None,
    min_confidence: Optional[float] = None
) -> Optional[Dict[str, Any]]:
    """
    Detect biển số trên crop của phương tiện (fallback khi không tìm thấy từ frame chính).

    Args:
        detector: YOLO detector instance
        frame: Frame gốc
        vehicle_det: Vehicle detection dict
        camera_id: ID camera để lấy detection_rules (optional)
        min_confidence: Min confidence threshold (nếu không có sẽ lấy từ camera hoặc settings)
    """
    if detector is None:
        return None

    try:
        # Lấy minConfidence từ tham số hoặc từ camera detection_rules hoặc settings
        conf_threshold = min_confidence
        if conf_threshold is None and camera_id:
            conf_threshold = _get_camera_min_confidence(camera_id)

        # Fallback về settings nếu không có
        if conf_threshold is None:
            conf_threshold = settings.YOLO_CONFIDENCE

        vx1, vy1, vx2, vy2 = map(int, vehicle_det.get("bbox", [0, 0, 0, 0]))
        h, w = frame.shape[:2]
        vx1, vy1 = max(0, vx1), max(0, vy1)
        vx2, vy2 = min(w, vx2), min(h, vy2)
        vehicle_crop = frame[vy1:vy2, vx1:vx2]

        if vehicle_crop.size == 0:
            return None

        crop_detections = detector.detect(
            vehicle_crop,
            conf=conf_threshold,
            iou=settings.YOLO_IOU_THRESHOLD
        )
        for det in crop_detections:
            if det.get("class_name") == "license_plate":
                cx1, cy1, cx2, cy2 = det.get("bbox", [0, 0, 0, 0])
                return {
                    "bbox": [
                        cx1 + vx1,
                        cy1 + vy1,
                        cx2 + vx1,
                        cy2 + vy1
                    ],
                    "confidence": det.get("confidence"),
                    "class_name": "license_plate"
                }
    except Exception as error:
        logger.warning(f"Không detect được plate trên ảnh xe: {error}")

    return None
