"""
Violation Creator - Tạo violation records

Chức năng:
- Tạo violation records với 3 ảnh (full, vehicle crop, plate crop)
- Extract thông tin từ detections
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta

from ...utils.image import crop_bbox, encode_image_base64
from ...utils.logger import app_logger as logger
from ..license_plate.detector import recognize_plate_text

# Timezone Vietnam (UTC+7)
VIETNAM_TZ = timezone(timedelta(hours=7))


def get_vietnam_time_for_db():
    """
    Lấy thời gian Vietnam NAIVE (không timezone) để lưu MongoDB

    MongoDB sẽ coi naive datetime là UTC, nên ta cần lưu Vietnam time
    dưới dạng naive datetime để khi đọc ra sẽ hiển thị đúng giờ VN.

    Returns:
        Naive datetime representing Vietnam time
    """
    # Lấy thời gian hiện tại UTC+7
    vn_time = datetime.now(VIETNAM_TZ)

    # Convert sang naive datetime (bỏ timezone info)
    # MongoDB sẽ lưu giá trị này và coi là UTC
    return vn_time.replace(tzinfo=None)


def create_violation_record(
    frame,
    vehicle_det: Dict[str, Any],
    plate_det: Optional[Dict[str, Any]],
    camera_id: str,
    camera_name: Optional[str] = None,
    location: Optional[str] = None,
    track_id: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Tạo record vi phạm với ảnh

    Args:
        frame: Frame gốc
        vehicle_det: Detection của phương tiện (có track_id)
        plate_det: Detection của biển số (nếu có)
        camera_id: ID camera
        camera_name: Tên camera
        location: Vị trí camera
        track_id: ID từ object tracker

    Returns:
        Dict violation record hoặc None nếu lỗi
    """
    try:
        # Extract thông tin từ detections
        vehicle_type = vehicle_det["class_name"]
        bbox = vehicle_det["bbox"]
        confidence = vehicle_det["confidence"]

        # Encode ảnh toàn cảnh
        full_frame_b64 = encode_image_base64(frame, quality=100)
        if not full_frame_b64:
            return None

        # Crop ảnh xe
        vehicle_crop = crop_bbox(frame, bbox, padding=10)
        vehicle_crop_b64 = encode_image_base64(vehicle_crop, quality=95) if vehicle_crop is not None else None

        # Crop ảnh biển số và OCR (nếu có)
        plate_crop_b64 = None
        plate_text = None
        if plate_det:
            plate_crop = crop_bbox(frame, plate_det["bbox"], padding=5)
            if plate_crop is not None:
                # OCR biển số
                plate_text = recognize_plate_text(plate_crop)
                # Encode ảnh gốc
                plate_crop_b64 = encode_image_base64(plate_crop, quality=95)

        # Tạo record - chỉ thông tin cần thiết
        violation = {
            "timestamp": get_vietnam_time_for_db(),  # Vietnam time (naive for MongoDB)
            "camera_id": camera_id,
            "camera_name": camera_name,
            "location": location,
            "vehicle_type": vehicle_type,
            "license_plate": plate_text,  # OCR result từ YOLO character detection
            "track_id": track_id,
            "violation_type": "roi_entry",
            "bbox": bbox,
            "confidence": confidence,
            "status": "detected",
            "images": {
                "full_frame": full_frame_b64,
                "vehicle_crop": vehicle_crop_b64,
                "plate_crop": plate_crop_b64
            }
        }

        return violation

    except Exception as e:
        logger.error(f"Lỗi tạo violation record: {e}")
        return None
