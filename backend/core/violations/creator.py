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

        # VẼ BBOX ĐỎ + TRAJECTORY cho xe vi phạm
        frame_with_text = frame.copy()

        # 1. Vẽ thông tin góc trái trên
        if location or camera_name:
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

        # 2. VẼ BBOX ĐỎ cho phương tiện vi phạm
        x1, y1, x2, y2 = map(int, bbox)
        cv2.rectangle(
            frame_with_text,
            (x1, y1),
            (x2, y2),
            (0, 0, 255),  # Màu đỏ (BGR)
            3  # Độ dày 3px
        )

        # 3. VẼ HƯỚNG DI CHUYỂN (trajectory)
        if track_id:
            try:
                from ..tracking.trajectory_tracker import get_trajectory_tracker
                tracker = get_trajectory_tracker(camera_id)
                trajectory = tracker.get_trajectory(track_id)

                if trajectory and len(trajectory.points) >= 2:
                    # Vẽ trajectory line (đường đi)
                    points = trajectory.get_points()
                    for i in range(len(points) - 1):
                        pt1 = (int(points[i].x), int(points[i].y))
                        pt2 = (int(points[i + 1].x), int(points[i + 1].y))
                        cv2.line(frame_with_text, pt1, pt2, (0, 0, 255), 2)  # Đỏ

                    # Vẽ mũi tên hướng (nếu có direction vector)
                    direction = trajectory.get_direction_vector()
                    if direction:
                        dx, dy = direction
                        # Normalize và scale
                        length = (dx**2 + dy**2)**0.5
                        if length > 0:
                            dx, dy = dx / length, dy / length
                            # Điểm cuối trajectory
                            last_pt = points[-1]
                            start = (int(last_pt.x), int(last_pt.y))
                            # Mũi tên dài 40px
                            end = (int(last_pt.x + dx * 40), int(last_pt.y + dy * 40))
                            cv2.arrowedLine(frame_with_text, start, end, (0, 0, 255), 3, tipLength=0.3)
            except Exception:
                pass  # Bỏ qua nếu không vẽ được trajectory

        # Encode ảnh toàn cảnh với quality thấp hơn để giảm lag (80 thay vì 100)
        # Quality 80 vẫn đủ rõ cho mục đích giám sát, nhưng giảm 50-60% kích thước file
        full_frame_b64 = encode_image_base64(frame_with_text, quality=80)
        if not full_frame_b64:
            return None

        # Crop ảnh xe với quality 85 (giảm từ 95)
        vehicle_crop = crop_bbox(frame, bbox, padding=10)
        vehicle_crop_b64 = encode_image_base64(vehicle_crop, quality=85) if vehicle_crop is not None else None

        # Crop ảnh biển số và OCR
        plate_crop_b64 = None
        plate_text = None

        # BƯỚC 1: Kiểm tra có plate detection từ stream không
        if plate_det:
            plate_crop = crop_bbox(frame, plate_det["bbox"], padding=5)
            if plate_crop is not None:
                # OCR biển số
                plate_text = recognize_plate_text(plate_crop)
                # Encode ảnh gốc với quality 85 để giảm lag
                plate_crop_b64 = encode_image_base64(plate_crop, quality=85)

        # BƯỚC 2: Nếu không có plate từ stream, TỰ ĐỘNG detect từ vehicle crop
        if plate_crop_b64 is None and vehicle_crop is not None:
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
                except Exception:
                    pass

                # GIẢM CONFIDENCE cho plate detection (plate thường nhỏ, dễ bị miss)
                if min_confidence is None:
                    from ...config.config import settings
                    min_confidence = settings.YOLO_CONFIDENCE

                # Giảm confidence 0.1 so với vehicle detection để tăng recall
                plate_conf = max(0.2, min_confidence - 0.1) if min_confidence else 0.3

                crop_detections = detector.detect(vehicle_crop, conf=plate_conf)

                # Tìm license_plate trong detections
                plate_det_from_crop = None
                for det in crop_detections:
                    if det.get("class_name") == "license_plate":
                        plate_det_from_crop = det
                        break

                if plate_det_from_crop:
                    # Crop plate từ vehicle crop (bbox đã relative to vehicle crop)
                    plate_bbox = plate_det_from_crop["bbox"]
                    px1, py1, px2, py2 = map(int, plate_bbox)
                    px1, py1 = max(0, px1), max(0, py1)
                    px2, py2 = min(vehicle_crop.shape[1], px2), min(vehicle_crop.shape[0], py2)
                    plate_crop = vehicle_crop[py1:py2, px1:px2]

                    if plate_crop.size > 0:
                        # OCR biển số với model license_plate (server.yaml line 27-32)
                        plate_text = recognize_plate_text(plate_crop)

                        if plate_text:
                            logger.info(f"✅ Plate OCR: {plate_text} (track={track_id})")

                        # Encode ảnh plate crop với quality 85
                        plate_crop_b64 = encode_image_base64(plate_crop, quality=85)

            except Exception as e:
                logger.error(f"❌ Plate detection error: {e}")

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
