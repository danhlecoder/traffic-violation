"""
Red Light Violation Recorder - Ghi nhận vi phạm vượt đèn đỏ

Điều kiện vi phạm:
1. Có đèn đỏ (class_name == 'light_red') trong frame
2. y2 (đáy bbox xe) nằm trong vùng STOPLINE_DETECTION_RANGE
3. y2 <= stopline_y (đã vượt vào vùng cấm)
4. **HƯỚNG DI CHUYỂN: Trục Y GIẢM DẦN** (xe đi xuống/tiến về stopline)
5. **KHÔNG RẼ PHẢI** (nếu rẽ phải thì được phép đi, không vi phạm)

Xử lý:
- Phát hiện hướng di chuyển từ trajectory (dy < 0 = đi xuống)
- Phát hiện rẽ phải (dx > threshold và angle phù hợp)
- Xóa vi phạm đã ghi nếu phát hiện xe rẽ phải
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
from .repository import upsert_violation_record, remove_violation_tag
from ..events.violation_broker import emit_violation_event
from ..tracking.trajectory_tracker import get_trajectory_tracker


class RedLightViolationRecorder:
    """Xử lý vi phạm vượt đèn đỏ với phát hiện hướng di chuyển."""

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
        # Lưu track_id đã vi phạm để detect rẽ phải sau
        self._flagged_tracks: Dict[str, bool] = {}

    def _has_red_light(self, detections: List[Dict[str, Any]]) -> bool:
        """Kiểm tra có đèn đỏ trong frame không"""
        for det in detections:
            if det.get("class_name") == "light_red":
                return True
        return False

    def _is_moving_down(self, track_id: str) -> bool:
        """
        Kiểm tra xe có đi xuống (y giảm dần) không
        Returns: True nếu dy < 0 (đi xuống về phía stopline)
        """
        trajectory = self.tracker.get_trajectory(track_id)
        if not trajectory or len(trajectory.points) < 2:
            return True  # Không đủ data → coi như đi thẳng (default)

        direction = trajectory.get_direction_vector()
        if direction is None:
            return True

        dx, dy = direction
        # dy < 0 = đi xuống (về phía stopline ở dưới)
        # dy > 0 = đi lên (ra xa stopline)
        return dy < 0

    def _is_turning_right(self, track_id: str) -> bool:
        """
        Phát hiện xe rẽ phải dựa vào trajectory

        Điều kiện rẽ phải:
        - dx > 0 (di chuyển sang phải)
        - |dx| > threshold (di chuyển ngang đủ lớn)
        - Tỉ lệ dx/dy cho thấy xu hướng rẽ (không chỉ lệch nhẹ)

        Returns: True nếu xe đang rẽ phải
        """
        trajectory = self.tracker.get_trajectory(track_id)
        if not trajectory or len(trajectory.points) < 3:
            return False  # Không đủ data

        direction = trajectory.get_direction_vector()
        if direction is None:
            return False

        dx, dy = direction

        # Ngưỡng: di chuyển ngang tối thiểu (pixels)
        MIN_HORIZONTAL_MOVEMENT = 30.0

        # Điều kiện 1: Di chuyển sang phải
        if dx <= 0:
            return False

        # Điều kiện 2: Di chuyển ngang đủ lớn
        if abs(dx) < MIN_HORIZONTAL_MOVEMENT:
            return False

        # Điều kiện 3: Tỉ lệ dx/dy cho thấy rẽ (không chỉ đi thẳng lệch nhẹ)
        # Nếu |dy| quá nhỏ so với |dx| → chắc chắn rẽ ngang
        # Nếu |dx|/|dy| > 0.5 → xu hướng rẽ phải rõ ràng
        if abs(dy) < 0.1:  # dy gần 0 → đi ngang hoàn toàn
            return True

        ratio = abs(dx) / abs(dy)
        IS_TURNING_RIGHT = ratio > 0.5  # dx chiếm > 50% so với dy
        return IS_TURNING_RIGHT

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

            # Đảm bảo đã vượt vào vùng cấm (y2 <= stopline)
            if y2 > stopline_y:
                continue

            # ✅ ĐIỀU KIỆN MỚI 1: Kiểm tra hướng di chuyển (phải đi XUỐNG)
            is_moving_down = self._is_moving_down(track_id)
            if not is_moving_down:
                continue

            # ✅ ĐIỀU KIỆN MỚI 2: Kiểm tra RẼ PHẢI (nếu rẽ phải → KHÔNG vi phạm đèn đỏ)
            is_turning_right = self._is_turning_right(track_id)
            if is_turning_right:
                # Nếu đã ghi nhận vi phạm đèn đỏ trước đó → CHỈ XÓA TAG "red_light"
                # GIỮ NGUYÊN các vi phạm khác (stopline_crossing, speed_violation, etc.)
                if self._flagged_tracks.get(track_id, False):
                    try:
                        removed = remove_violation_tag(track_id, "red_light")
                        if removed:
                            logger.info(f"🗑️ Xóa tag 'red_light' của {track_id} (rẽ phải)")
                            self._flagged_tracks[track_id] = False
                    except Exception as e:
                        logger.error(f"❌ Lỗi xóa tag red_light: {e}")
                continue

            # Tất cả điều kiện đều thỏa → GHI NHẬN VI PHẠM
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
                logger.info(f"🚦 Red light: {track_id}")
                # Đánh dấu đã ghi nhận
                self._flagged_tracks[track_id] = True

                event_payload = {
                    "action": action,
                    "type": "red_light",
                    "track_id": track_id,
                    "camera_id": self.camera_id,
                }
                if action == "created" and result != track_id:
                    event_payload["db_id"] = result
                emit_violation_event(event_payload)






