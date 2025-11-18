"""
Detection Record Creator - Tạo detection records

Chức năng:
- Tạo detection records với 3 ảnh (full, vehicle crop, plate crop)
- Extract thông tin từ detections
- Đánh dấu tất cả phương tiện là "detected" (chưa xử lý vi phạm)
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import cv2

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
    track_id: Optional[str] = None,  # Format: 5 ký tự alphanumeric + hhmmss
    speed_kmh: Optional[float] = None,  # Tốc độ tính bằng km/h
    violation_type: str = "detected",  # Deprecated: Dùng violation_tags thay thế
) -> Optional[Dict[str, Any]]:
    """
    Tạo detection record với ảnh

    Args:
        frame: Frame gốc
        vehicle_det: Detection của phương tiện (có track_id)
        plate_det: Detection của biển số (nếu có)
        camera_id: ID camera
        camera_name: Tên camera
        location: Vị trí camera
        track_id: ID từ object tracker

    Returns:
        Dict detection record hoặc None nếu lỗi
    """
    try:
        # Extract thông tin từ detections
        vehicle_type = vehicle_det["class_name"]
        bbox = vehicle_det["bbox"]
        confidence = vehicle_det["confidence"]

        # Vẽ thông tin vị trí và thời gian ở góc trái trên (chỉ khi cần)
        # Tạo copy chỉ khi cần vẽ text để tránh modify frame gốc và tiết kiệm memory
        frame_with_text = frame
        if location or camera_name:
            frame_with_text = frame.copy()
            # Vị trí (dòng 1)
            text_location = location or camera_name or "Unknown"
            cv2.putText(
                frame_with_text,
                text_location,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
                cv2.LINE_AA
            )

            # Thời gian (dòng 2) - Giờ Việt Nam (UTC+7)
            current_time = datetime.now(VIETNAM_TZ).strftime("%d-%m-%Y %H:%M:%S")
            cv2.putText(
                frame_with_text,
                current_time,
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
                cv2.LINE_AA
            )

        # Encode ảnh toàn cảnh (đã có text nếu có)
        full_frame_b64 = encode_image_base64(frame_with_text, quality=100)
        if not full_frame_b64:
            return None

        # Crop ảnh xe
        vehicle_crop = crop_bbox(frame, bbox, padding=10)
        vehicle_crop_b64 = encode_image_base64(vehicle_crop, quality=95) if vehicle_crop is not None else None

        # Crop ảnh biển số và OCR
        plate_crop_b64 = None
        plate_text = None

        # BƯỚC 1: Kiểm tra có plate detection từ stream không
        if plate_det:
            logger.debug(f"Có plate detection từ stream")
            plate_crop = crop_bbox(frame, plate_det["bbox"], padding=5)
            if plate_crop is not None:
                # OCR biển số
                plate_text = recognize_plate_text(plate_crop)
                if plate_text:
                    logger.debug(f"OCR: {plate_text}")
                # Encode ảnh gốc
                plate_crop_b64 = encode_image_base64(plate_crop, quality=95)
            else:
                logger.debug("Plate crop failed")

        # BƯỚC 2: Nếu không có plate từ stream, TỰ ĐỘNG detect từ vehicle crop
        if plate_crop_b64 is None and vehicle_crop is not None:
            logger.debug("Tự động detect plate từ vehicle crop...")
            try:
                from ..detection.yolo import get_yolo_detector
                detector = get_yolo_detector()

                # Lấy minConfidence từ camera detection_rules (nếu có)
                min_confidence = None
                try:
                    from ...api.clients.mongodb_service import get_mongodb_service
                    service = get_mongodb_service()
                    camera = service.get_camera(camera_id)
                    if camera and camera.get("detection_rules") and camera["detection_rules"].get("minConfidence"):
                        min_confidence = float(camera["detection_rules"]["minConfidence"])
                except Exception as e:
                    logger.debug(f"Không lấy được detection_rules từ camera {camera_id}: {e}")

                # Fallback về settings nếu không có
                if min_confidence is None:
                    from ...config.config import settings
                    min_confidence = settings.YOLO_CONFIDENCE

                # Detect plate trực tiếp trên vehicle crop
                logger.debug(f"Đang detect plate trên vehicle crop với conf={min_confidence}")
                crop_detections = detector.detect(vehicle_crop, conf=min_confidence)

                # Tìm license_plate trong detections
                plate_det_from_crop = None
                for det in crop_detections:
                    if det.get("class_name") == "license_plate":
                        plate_det_from_crop = det
                        break

                if plate_det_from_crop:
                    logger.debug(f"Detect plate từ vehicle crop OK")
                    # Crop plate từ vehicle crop (bbox đã relative to vehicle crop)
                    plate_bbox = plate_det_from_crop["bbox"]
                    px1, py1, px2, py2 = map(int, plate_bbox)
                    px1, py1 = max(0, px1), max(0, py1)
                    px2, py2 = min(vehicle_crop.shape[1], px2), min(vehicle_crop.shape[0], py2)
                    plate_crop = vehicle_crop[py1:py2, px1:px2]

                    if plate_crop.size > 0:
                        # OCR biển số
                        plate_text = recognize_plate_text(plate_crop)
                        if plate_text:
                            logger.debug(f"OCR từ vehicle crop: {plate_text}")
                        # Encode ảnh plate crop
                        plate_crop_b64 = encode_image_base64(plate_crop, quality=95)
            except Exception as e:
                logger.error(f"❌ Lỗi khi detect plate từ vehicle crop: {e}", exc_info=True)

        # Tạo record - chỉ thông tin cần thiết
        # Convert datetime sang ISO string để serialize JSON
        timestamp = get_vietnam_time_for_db().isoformat()

        # Tạo violation_tags từ violation_type (backward compatibility)
        violation_tags = [violation_type] if violation_type else ["detected"]

        violation = {
            "timestamp": timestamp,  # ISO string format (YYYY-MM-DDTHH:MM:SS)
            "camera_id": camera_id,
            "camera_name": camera_name,
            "location": location,
            "vehicle_type": vehicle_type,
            "license_plate": plate_text,  # OCR result từ YOLO character detection
            "track_id": track_id,
            "violation_tags": violation_tags,  # Dùng violation_tags thay vì violation_type
            "bbox": bbox,
            "confidence": confidence,
            "status": "detected",
            "speed": speed_kmh,  # Tốc độ tính bằng km/h (nếu có)
            "images": {
                "full_frame": full_frame_b64,
                "vehicle_crop": vehicle_crop_b64,
                "plate_crop": plate_crop_b64
            }
        }
        violation["violation_history"] = [
            {
                "type": violation_tags[0],  # Lấy tag đầu tiên cho history
                "timestamp": timestamp,
                "speed": speed_kmh,
            }
        ]

        return violation

    except Exception as e:
        logger.error(f"Lỗi tạo violation record: {e}")
        return None
