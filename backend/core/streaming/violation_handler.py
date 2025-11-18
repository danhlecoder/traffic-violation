"""
Violation Handler - Xử lý phát hiện vi phạm stopline
Tách logic violation detection ra khỏi mjpeg.py
"""

from typing import List, Dict, Any, Optional
import time
import numpy as np
from ...utils.logger import stream_logger as logger
from ...config.config import settings
from ..constants import VEHICLE_CLASSES
from ..tracking.stopline_tracker import get_stopline_crossing_detector
from ..violations.creator import create_violation_record
from ..violations.repository import upsert_violation_record
from ...utils.violations import find_plate_detection_for_vehicle, detect_plate_on_vehicle_crop
from ...api.clients.mongodb_service import get_mongodb_service


def process_stopline_violations(
    frame: np.ndarray,
    detections: List[Dict[str, Any]],
    stopline: Optional[Dict[str, Any]],
    stopline_detector,
    detector,
    camera_id: str,
    camera_name: Optional[str],
    location: Optional[str],
    trajectory_tracker=None
) -> int:
    """
    Xử lý phát hiện vi phạm vượt stopline

    Args:
        frame: Frame hiện tại
        detections: Danh sách detections
        stopline: Stopline config dict
        stopline_detector: StoplineCrossingDetector instance
        detector: YOLO detector instance
        camera_id: ID camera
        camera_name: Tên camera
        location: Vị trí camera

    Returns:
        Số lượng violations đã tạo
    """
    if not stopline_detector or not stopline or not detections:
        return 0

    try:
        if not isinstance(stopline, dict) or "y" not in stopline:
            logger.error(f"Stopline format sai: {type(stopline)}")
            return 0

        stopline_y_raw = float(stopline["y"])
        is_normalized = stopline.get("is_normalized", False)
        frame_height = frame.shape[0]

        if is_normalized:
            stopline_y = stopline_y_raw * frame_height
        else:
            stopline_y = stopline_y_raw

        # Cache các giá trị tính toán để tránh tính lại mỗi detection
        detection_min = stopline_y - settings.STOPLINE_DETECTION_RANGE
        detection_max = stopline_y + settings.STOPLINE_DETECTION_RANGE
        frame_width = frame.shape[1]
        frame_center_x = frame_width / 2

        record_count = 0
        camera_min_confidence = None
        camera_rules_fetched = False

        for det in detections:
            if det["class_name"] not in VEHICLE_CLASSES:
                continue

            bbox = det.get("bbox")
            if not bbox or len(bbox) != 4:
                continue

            x1, y1, x2, y2 = bbox

            # Kiểm tra xe có trong vùng detection range không (điều kiện chính)
            is_in_range = detection_min <= y2 <= detection_max

            if not is_in_range:
                continue  # Xe ngoài vùng detection, bỏ qua

            # Xác định phương tiện ở phía bên phải (điều kiện bắt buộc)
            center_x = (x1 + x2) / 2
            is_right_side = center_x >= frame_center_x

            if not is_right_side:
                track_id = det.get("track_id", "?")
                logger.debug(f"⏭️  Track {track_id}: Xe ở phía bên trái, bỏ qua (center_x={center_x:.1f}, frame_width={frame_width})")
                continue

            # Lấy track_id - BẮT BUỘC để tránh phát hiện nhiều lần cho cùng 1 phương tiện
            track_id = det.get("track_id")
            if not track_id:
                logger.warning(f"⚠️ Detection không có track_id, bỏ qua (vehicle: {det.get('class_name')})")
                continue  # Bỏ qua nếu không có track_id - đảm bảo mọi vehicle đều có track_id từ vehicle_tracker

            # Log debug khi xe trong vùng detection và ở phía bên phải (chỉ khi cần debug)
            distance_to_stopline = y2 - stopline_y
            logger.debug(
                f"Track {track_id}: y2={y2:.1f}px, stopline={stopline_y:.1f}px, "
                f"distance={distance_to_stopline:+.1f}px"
            )

            # Gọi check_crossing - sẽ ghi nhận ngay nếu is_in_range = True
            # track_id là string: 5 số ngẫu nhiên + hhmmss (đã được đảm bảo từ vehicle_tracker)
            is_crossing = stopline_detector.check_crossing(
                track_id=track_id,  # Giữ nguyên string format
                bbox=bbox,
                stopline_y=stopline_y
            )

            # Bỏ log debug không cần thiết

            if is_crossing:
                record_count += 1

                # Sử dụng hàm utility chung để tìm plate
                plate_det = find_plate_detection_for_vehicle(det, detections)
                if plate_det is None and detector:
                    if not camera_rules_fetched and camera_id:
                        camera_rules_fetched = True
                        try:
                            camera = get_mongodb_service().get_camera(camera_id)
                            rules = camera.get("detection_rules") if camera else None
                            min_conf = rules.get("minConfidence") if rules else None
                            if min_conf is not None:
                                camera_min_confidence = float(min_conf)
                        except Exception as exc:
                            logger.debug(f"Không lấy được detection_rules từ camera {camera_id}: {exc}")
                    plate_det = detect_plate_on_vehicle_crop(
                        detector,
                        frame,
                        det,
                        min_confidence=camera_min_confidence,
                    )

                # Lấy tốc độ từ trajectory tracker nếu có
                speed_kmh = None
                if trajectory_tracker:
                    try:
                        trajectory = trajectory_tracker.get_trajectory(track_id)
                        if trajectory:
                            points_count = len(trajectory.get_points())
                            line_offset_px = settings.TRAJECTORY_PIXELS_BETWEEN_LINES
                            pixels_per_meter = settings.PIXELS_PER_METER
                            if line_offset_px > 0 and pixels_per_meter > 0:
                                speed_kmh = trajectory.get_speed_kmh_through_stopline_gate(
                                    stopline_y=stopline_y,
                                    line_offset_pixels=line_offset_px,
                                    pixels_per_meter=pixels_per_meter,
                                )
                            if speed_kmh is not None:
                                logger.debug(f"Track {track_id}: Tốc độ = {speed_kmh:.1f} km/h")
                            else:
                                logger.debug(f"Track {track_id}: Không tính được tốc độ (cần nhiều điểm hơn)")
                    except Exception as e:
                        logger.debug(f"Không lấy được tốc độ cho track {track_id}: {e}")

                violation = create_violation_record(
                    frame=frame.copy(),
                    vehicle_det=det,
                    plate_det=plate_det,
                    track_id=track_id,
                    camera_id=camera_id,
                    camera_name=camera_name,
                    location=location,
                    speed_kmh=speed_kmh
                )

                if violation:
                    result = upsert_violation_record(violation)
                    if result:
                        action = "created" if result != track_id else "updated"
                        event_payload = {
                            "action": action,
                            "type": "stopline_crossing",
                            "track_id": track_id,
                            "camera_id": camera_id,
                        }
                        if action == "created" and result != track_id:
                            event_payload["db_id"] = result
                        emit_violation_event(event_payload)
                    elif track_id in stopline_detector.tracks:
                        stopline_detector.tracks[track_id]["crossed"] = False

        return record_count

    except Exception as e:
        logger.error(f"Lỗi stopline detection: {e}")
        return 0
