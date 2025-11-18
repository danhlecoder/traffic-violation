"""
Red Light Violation Recorder - Ghi nhận vi phạm vượt đèn đỏ

Điều kiện:
- Có detection đèn đỏ (class_name == 'light_red') trong frame hiện tại
- y2 (đáy bbox của xe) nằm trong vùng STOPLINE_DETECTION_RANGE quanh stopline_y
- Và y2 <= stopline_y (đã vượt vào vùng cấm khi đèn đỏ)

Chiến lược:
- Ưu tiên cập nhật theo track_id (nếu đã có record 'detected'): update violation_type, timestamp, ảnh mới nhất
- Nếu chưa có record: tạo mới bằng create_violation_record
"""

from typing import Dict, Any, List, Optional

from ...utils.logger import app_logger as logger
from ...config.config import settings
from ...utils.violations import (
    find_plate_detection_for_vehicle,
    detect_plate_on_vehicle_crop,
    normalize_stopline_y,
)
from ..constants import VEHICLE_CLASSES
from .creator import create_violation_record
from .repository import upsert_violation_record
from ..events.violation_broker import emit_violation_event
from ..tracking.trajectory_tracker import get_trajectory_tracker


class RedLightViolationRecorder:
    """Xử lý vi phạm vượt đèn đỏ."""

    def __init__(
        self,
        camera_id: str,
        camera_name: Optional[str] = None,
        location: Optional[str] = None,
    ) -> None:
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.location = location
        self.tracker = get_trajectory_tracker(camera_id)

    def _has_red_light(self, detections: List[Dict[str, Any]]) -> bool:
        for det in detections:
            if det.get("class_name") == "light_red":
                return True
        return False

    def process(
        self,
        frame,
        detections: List[Dict[str, Any]],
        stopline: Dict[str, Any],
        detector,
    ) -> None:
        if not detections or not stopline:
            return

        if not self._has_red_light(detections):
            return

        stopline_y = normalize_stopline_y(stopline, frame.shape[0])
        if stopline_y is None:
            return

        detection_min = stopline_y - settings.STOPLINE_DETECTION_RANGE
        detection_max = stopline_y
        pixels_per_meter = float(settings.PIXELS_PER_METER)
        line_offset_px = float(settings.TRAJECTORY_PIXELS_BETWEEN_LINES)

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

            # đảm bảo đã vượt vào vùng cấm (y2 <= stopline)
            if y2 > stopline_y:
                continue

            plate_det = find_plate_detection_for_vehicle(det, detections)
            if plate_det is None:
                plate_det = detect_plate_on_vehicle_crop(detector, frame, det)

            speed_kmh = None
            if pixels_per_meter > 0 and line_offset_px > 0:
                trajectory = self.tracker.get_trajectory(track_id)
                if trajectory:
                    speed_kmh = trajectory.get_speed_kmh_through_stopline_gate(
                        stopline_y=stopline_y,
                        line_offset_pixels=line_offset_px,
                        pixels_per_meter=pixels_per_meter,
                    )

            violation = create_violation_record(
                frame=frame.copy(),
                vehicle_det=det,
                plate_det=plate_det,
                track_id=track_id,
                camera_id=self.camera_id,
                camera_name=self.camera_name,
                location=self.location,
                speed_kmh=speed_kmh,
                violation_type="red_light",
            )
            if not violation:
                continue

            result = upsert_violation_record(violation)
            if result:
                action = "created" if result != track_id else "updated"
                logger.info(
                    f"🚦 [RedLight] {'Tạo' if action == 'created' else 'Cập nhật'} vi phạm vượt đèn đỏ: track_id={track_id}"
                )
                event_payload = {
                    "action": action,
                    "type": "red_light",
                    "track_id": track_id,
                    "camera_id": self.camera_id,
                }
                if action == "created" and result != track_id:
                    event_payload["db_id"] = result
                emit_violation_event(event_payload)




