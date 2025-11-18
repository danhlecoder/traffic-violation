"""
Stopline Violation Recorder - Quản lý ghi nhận phương tiện vượt vạch dừng
"""

from typing import Dict, Any, List, Optional

from ...utils.logger import app_logger as logger
from ...config.config import settings
from ..tracking.stopline_tracker import get_stopline_crossing_detector
from .creator import create_violation_record
from .repository import upsert_violation_record
from ..events.violation_broker import emit_violation_event
from ...utils.violations import (
    normalize_stopline_y,
    find_plate_detection_for_vehicle,
    detect_plate_on_vehicle_crop,
)
from ..constants import VEHICLE_CLASSES


class StoplineViolationRecorder:
    """Ghi nhận phương tiện vượt stopline để tạo record vi phạm."""

    def __init__(
        self,
        camera_id: str,
        camera_name: Optional[str] = None,
        location: Optional[str] = None,
    ) -> None:
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.location = location
        self.detector = get_stopline_crossing_detector(camera_id)

    def process(
        self,
        frame,
        detections: List[Dict[str, Any]],
        stopline: Dict[str, Any],
        detector,
    ) -> None:
        """
        Kiểm tra từng detection và lưu vi phạm vượt stopline khi thoả điều kiện.
        """
        if not stopline or not detections:
            return

        stopline_y = normalize_stopline_y(stopline, frame.shape[0])
        if stopline_y is None:
            logger.error("Stopline không hợp lệ, bỏ qua xử lý stopline")
            return

        detection_min = stopline_y - settings.STOPLINE_DETECTION_RANGE
        detection_max = stopline_y

        for det in detections:
            if det.get("class_name") not in VEHICLE_CLASSES:
                continue
            track_id = det.get("track_id")
            bbox = det.get("bbox")
            if track_id is None or not bbox or len(bbox) != 4:
                continue

            _, _, _, y2 = bbox
            if not (detection_min <= y2 <= detection_max):
                continue

            distance_to_stopline = y2 - stopline_y
            logger.info(
                (
                    f"🚗 Track {track_id}: y2={y2:.1f}px, stopline={stopline_y:.1f}px, "
                    f"distance={distance_to_stopline:+.1f}px (vùng:{detection_min:.1f}-{detection_max:.1f})"
                )
            )

            if not self.detector.check_crossing(track_id=track_id, bbox=bbox, stopline_y=stopline_y):
                continue

            plate_det = find_plate_detection_for_vehicle(det, detections)
            if plate_det is None:
                plate_det = detect_plate_on_vehicle_crop(detector, frame, det)

            violation = create_violation_record(
                frame=frame.copy(),
                vehicle_det=det,
                plate_det=plate_det,
                track_id=track_id,
                camera_id=self.camera_id,
                camera_name=self.camera_name,
                location=self.location,
                violation_type="stopline_crossing",
            )
            if not violation:
                continue
            result = upsert_violation_record(violation)
            if result:
                action = "created" if result != track_id else "updated"
                event_payload = {
                    "action": action,
                    "type": "stopline_crossing",
                    "track_id": track_id,
                    "camera_id": self.camera_id,
                }
                if action == "created" and result != track_id:
                    event_payload["db_id"] = result
                emit_violation_event(event_payload)
