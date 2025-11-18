"""
Helmet Violation Recorder - Phát hiện phương tiện không đội mũ bảo hiểm.

Điều kiện:
- Detection phương tiện là motorcycle (có track_id).
- Có detection `no_helmet` nằm bên trong bbox của motorcycle.

Chiến lược:
- Ưu tiên cập nhật bản ghi theo track_id thông qua upsert (tránh trùng duplicate id).
- Lấy ảnh, biển số tương tự các bộ ghi nhận vi phạm khác.
"""

from typing import Dict, Any, List, Optional

from ...utils.logger import app_logger as logger
from .creator import create_violation_record
from .repository import upsert_violation_record
from ..events.violation_broker import emit_violation_event
from ...utils.violations import (
    find_plate_detection_for_vehicle,
    detect_plate_on_vehicle_crop,
)


class NoHelmetViolationRecorder:
    """Ghi nhận vi phạm không đội mũ bảo hiểm cho xe máy."""

    def __init__(
        self,
        camera_id: str,
        camera_name: Optional[str] = None,
        location: Optional[str] = None,
    ) -> None:
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.location = location

    @staticmethod
    def _is_no_helmet_inside_vehicle(
        vehicle_det: Dict[str, Any],
        helmet_det: Dict[str, Any],
    ) -> bool:
        """Kiểm tra bbox no_helmet có nằm trong bbox xe máy không."""
        vbbox = vehicle_det.get("bbox")
        hbbox = helmet_det.get("bbox")
        if not vbbox or not hbbox or len(vbbox) != 4 or len(hbbox) != 4:
            return False

        vx1, vy1, vx2, vy2 = vbbox
        hx1, hy1, hx2, hy2 = hbbox

        # Sử dụng tâm bbox để tránh vấn đề do scale
        hcx = (hx1 + hx2) / 2
        hcy = (hy1 + hy2) / 2
        return vx1 <= hcx <= vx2 and vy1 <= hcy <= vy2

    def _find_no_helmet_detection(
        self,
        vehicle_det: Dict[str, Any],
        detections: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """Tìm detection no_helmet bên trong bbox của xe máy."""
        for det in detections:
            if det.get("class_name") != "no_helmet":
                continue
            if self._is_no_helmet_inside_vehicle(vehicle_det, det):
                return det
        return None

    def process(
        self,
        frame,
        detections: List[Dict[str, Any]],
        detector,
    ) -> None:
        """
        Duyệt các detections, tạo/cập nhật record vi phạm khi có no_helmet bên trong xe máy.
        """
        if not detections:
            return

        for vehicle_det in detections:
            if vehicle_det.get("class_name") != "motorcycle":
                continue

            track_id = vehicle_det.get("track_id")
            if not track_id:
                continue

            if not self._find_no_helmet_detection(vehicle_det, detections):
                continue

            plate_det = find_plate_detection_for_vehicle(vehicle_det, detections)
            if plate_det is None:
                plate_det = detect_plate_on_vehicle_crop(
                    detector,
                    frame,
                    vehicle_det,
                    camera_id=self.camera_id,
                )

            violation = create_violation_record(
                frame=frame.copy(),
                vehicle_det=vehicle_det,
                plate_det=plate_det,
                track_id=track_id,
                camera_id=self.camera_id,
                camera_name=self.camera_name,
                location=self.location,
                violation_type="no_helmet",
            )
            if not violation:
                continue

            result = upsert_violation_record(violation)
            if result:
                action = "created" if result != track_id else "updated"
                logger.info(
                    f"🪖 [Helmet] {'Tạo' if action == 'created' else 'Cập nhật'} vi phạm không đội mũ:"
                    f" track_id={track_id}"
                )
                event_payload = {
                    "action": action,
                    "type": "no_helmet",
                    "track_id": track_id,
                    "camera_id": self.camera_id,
                }
                if action == "created" and result != track_id:
                    event_payload["db_id"] = result
                emit_violation_event(event_payload)
