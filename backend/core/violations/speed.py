"""
Speed Violation Recorder - Quản lý ghi nhận phương tiện vi phạm tốc độ

Nguyên tắc:
- Dùng TrajectoryTracker để ước tính tốc độ (km/h) theo calibration pixels→meters.
- Lấy speedLimit và enableSpeedCheck từ detection_rules của camera.
- Nếu vượt ngưỡng, cố gắng cập nhật bản ghi theo track_id trước; nếu không có thì tạo record mới.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from ...utils.logger import app_logger as logger
from ...config.config import settings
from ..tracking.trajectory_tracker import get_trajectory_tracker
from ...api.clients.mongodb_service import get_mongodb_service
from .creator import create_violation_record
from .repository import upsert_violation_record
from ..events.violation_broker import emit_violation_event
from ...utils.violations import (
    find_plate_detection_for_vehicle,
    detect_plate_on_vehicle_crop,
    normalize_stopline_y,
)
from ..constants import VEHICLE_CLASSES
MIN_VALID_SPEED_KMH = 5.0


class SpeedViolationRecorder:
    """Ghi nhận phương tiện vi phạm tốc độ theo rule từng camera."""

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
        self.mongo = get_mongodb_service()
        # Chống spam cập nhật: lưu trạng thái gần nhất per track
        self._state: Dict[str, Dict[str, Any]] = {}
        self._update_interval_sec: float = 1.5  # tối thiểu 1.5s mới cập nhật lại
        self._min_speed_delta: float = 0.5      # thay đổi <0.5 km/h thì bỏ qua

    def _get_speed_limit(self) -> Optional[float]:
        """
        Lấy speedLimit từ detection_rules của camera.
        Trả None nếu không bật enableSpeedCheck hoặc không có limit.
        """
        try:
            camera = self.mongo.get_camera(self.camera_id)
            rules = camera.get("detection_rules") if camera else None
            if not rules:
                return None
            if not rules.get("enableSpeedCheck", False):
                return None
            limit = rules.get("speedLimit")
            return float(limit) if limit is not None else None
        except Exception as e:
            logger.error(f"Lỗi đọc detection_rules của camera {self.camera_id}: {e}")
            return None

    def process(
        self,
        frame,
        detections: List[Dict[str, Any]],
        detector,
        stopline: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Kiểm tra từng detection và lưu/cập nhật vi phạm tốc độ khi vượt ngưỡng.
        - Ước tính tốc độ theo trajectory (km/h)
        - So sánh với speedLimit từ camera rules
        - Nếu vượt, update theo track_id; nếu không tồn tại thì tạo mới
        """
        if not detections:
            return

        speed_limit = self._get_speed_limit()
        if speed_limit is None:
            return

        stopline_y_pixels = normalize_stopline_y(stopline, frame.shape[0]) if stopline else None
        pixels_per_meter = float(settings.PIXELS_PER_METER)
        line_offset_px = float(settings.TRAJECTORY_PIXELS_BETWEEN_LINES)

        for det in detections:
            if det.get("class_name") not in VEHICLE_CLASSES:
                continue
            track_id = det.get("track_id")
            bbox = det.get("bbox")
            if track_id is None or not bbox or len(bbox) != 4:
                continue

            trajectory = self.tracker.get_trajectory(track_id)
            if not trajectory:
                continue

            speed_kmh = None
            if stopline_y_pixels is not None and pixels_per_meter > 0 and line_offset_px > 0:
                speed_kmh = trajectory.get_speed_kmh_through_stopline_gate(
                    stopline_y=stopline_y_pixels,
                    line_offset_pixels=line_offset_px,
                    pixels_per_meter=pixels_per_meter,
                )
            if speed_kmh is None:
                continue

            # Bỏ qua tốc độ quá thấp hoặc không vượt ngưỡng
            if speed_kmh <= speed_limit or speed_kmh < MIN_VALID_SPEED_KMH:
                state = self._state.get(track_id)
                if state and state.get("flagged"):
                    state["flagged"] = False
                continue

            now = datetime.now()
            state = self._state.get(
                track_id,
                {"flagged": False, "last_time": datetime.fromtimestamp(0), "last_speed": 0.0},
            )

            elapsed = (now - state["last_time"]).total_seconds()
            speed_delta = abs(float(speed_kmh) - float(state.get("last_speed", 0.0)))
            should_update = (
                not state["flagged"]
                or (elapsed >= self._update_interval_sec and speed_delta >= self._min_speed_delta)
            )

            if not should_update:
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
                speed_kmh=float(speed_kmh),
                violation_type="speed_violation",
            )
            if not violation:
                continue

            # ✅ SỬ DỤNG ASYNC MODE để không block stream
            result = upsert_violation_record(violation, async_mode=True)
            if result:
                action = "created" if result != track_id else "updated"
                log_msg = (
                    f"🚨 [Speed] {'Tạo' if action == 'created' else 'Cập nhật'} vi phạm tốc độ:"
                    f" track_id={track_id}, speed={speed_kmh:.1f} km/h (> {speed_limit:.1f})"
                )
                logger.info(log_msg)
                event_payload = {
                    "action": action,
                    "type": "speed_violation",
                    "track_id": track_id,
                    "camera_id": self.camera_id,
                }
                if action == "created" and result != track_id:
                    event_payload["db_id"] = result
                emit_violation_event(
                    event_payload
                )
                self._state[track_id] = {"flagged": True, "last_time": now, "last_speed": float(speed_kmh)}
