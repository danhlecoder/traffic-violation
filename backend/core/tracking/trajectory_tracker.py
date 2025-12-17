"""
Trajectory Tracker - Truy vết hướng di chuyển của phương tiện

Chức năng:
- Track quỹ đạo di chuyển của mỗi vehicle theo track_id
- Lưu lịch sử vị trí (trajectory points) của từng xe
- Cleanup trajectories cũ tự động
- Hỗ trợ phân tích hướng di chuyển
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque

from ...utils.logger import app_logger as logger


@dataclass
class TrajectoryPoint:
    """Một điểm trên quỹ đạo di chuyển"""
    x: float  # Center x coordinate
    y: float  # Center y coordinate
    timestamp: datetime
    bbox: Tuple[float, float, float, float]  # [x1, y1, x2, y2]

    def __repr__(self):
        return f"Point({self.x:.1f}, {self.y:.1f})"


@dataclass
class VehicleTrajectory:
    """Quỹ đạo di chuyển của 1 phương tiện"""
    track_id: str  # Format: 5 ký tự alphanumeric + hhmmss
    points: deque = field(default_factory=deque)  # Trajectory points
    max_points: int = 30  # Số điểm tối đa giữ lại
    last_update: datetime = field(default_factory=datetime.now)

    def add_point(self, x: float, y: float, bbox: Tuple[float, float, float, float]):
        """Thêm điểm mới vào trajectory"""
        point = TrajectoryPoint(
            x=x,
            y=y,
            timestamp=datetime.now(),
            bbox=bbox
        )
        self.points.append(point)
        self.last_update = datetime.now()

        # Giữ số lượng points trong giới hạn
        while len(self.points) > self.max_points:
            self.points.popleft()

    def get_points(self) -> List[TrajectoryPoint]:
        """Lấy tất cả trajectory points"""
        return list(self.points)

    def get_recent_points(self, seconds: float = 3.0) -> List[TrajectoryPoint]:
        """Lấy các điểm trong N giây gần nhất"""
        cutoff = datetime.now() - timedelta(seconds=seconds)
        return [p for p in self.points if p.timestamp >= cutoff]

    def get_direction_vector(self) -> Optional[Tuple[float, float]]:
        """
        Tính vector hướng di chuyển trung bình
        Returns: (dx, dy) hoặc None nếu không đủ data
        """
        if len(self.points) < 2:
            return None

        # Lấy điểm đầu và cuối
        first = self.points[0]
        last = self.points[-1]

        dx = last.x - first.x
        dy = last.y - first.y

        return (dx, dy)

    # thời điểm xe cắt qua 2 vạch
    def _crossing_time(self, target_y: float) -> Optional[datetime]:
        pts = self.points
        for i in range(len(pts) - 1):
            p1, p2 = pts[i], pts[i + 1]
            if p1.y == target_y:
                return p1.timestamp
            if p2.y == target_y:
                return p2.timestamp
            if (p1.y - target_y) * (p2.y - target_y) < 0:
                dy = (p2.y - p1.y)
                if dy == 0:
                    continue
                ratio = (target_y - p1.y) / dy
                dt = p2.timestamp - p1.timestamp
                return p1.timestamp + (dt * ratio)
        return None

    # TODO: Tính đốc độ km/h
    def get_speed_kmh_between_lines(
        self,
        line_a_y: float,
        line_b_y: float,
        pixels_per_meter: float,
    ) -> Optional[float]:
        if len(self.points) < 2 or pixels_per_meter <= 0 or line_a_y == line_b_y:
            return None

        t_a = self._crossing_time(line_a_y)
        t_b = self._crossing_time(line_b_y)

        if t_a is None or t_b is None or t_a == t_b:
            return None

        delta_s = abs((t_b - t_a).total_seconds())
        if delta_s <= 0:
            return None

        distance_px = abs(line_a_y - line_b_y)
        distance_m = distance_px / pixels_per_meter
        if distance_m <= 0:
            return None

        speed_m_s = distance_m / delta_s
        speed_kmh = speed_m_s * 3.6
        if speed_kmh < 0.5:
            return 0.0
        return speed_kmh

    # TODO: Tạo lineB
    def get_speed_kmh_through_stopline_gate(
        self,
        stopline_y: float,
        line_offset_pixels: float,
        pixels_per_meter: float,
    ) -> Optional[float]:
        if line_offset_pixels == 0:
            return None

        # Mặc định lineB nằm phía trên stopline (y nhỏ hơn)
        primary = self.get_speed_kmh_between_lines(
            stopline_y,
            stopline_y - line_offset_pixels,
            pixels_per_meter,
        )
        if primary is not None:
            return primary

        # Nếu không tìm được, thử hướng ngược lại (line nằm phía dưới stopline)
        return self.get_speed_kmh_between_lines(
            stopline_y,
            stopline_y + line_offset_pixels,
            pixels_per_meter,
        )


class TrajectoryTracker:
    """
    Quản lý trajectory của tất cả vehicles

    Features:
    - Track trajectory cho mỗi vehicle (theo track_id)
    - Auto cleanup trajectories cũ
    - Phân tích hướng di chuyển

    Config:
    - max_trajectory_points: Số điểm tối đa mỗi trajectory
    - cleanup_timeout: Thời gian (giây) để cleanup trajectory không update
    """

    def __init__(
        self,
        camera_id: str,
        max_trajectory_points: int = 30,
        cleanup_timeout: int = 30
    ):
        """
        Args:
            camera_id: ID camera
            max_trajectory_points: Số điểm tối đa cho mỗi trajectory
            cleanup_timeout: Cleanup trajectories không update trong X giây
        """
        self.camera_id = camera_id
        self.max_trajectory_points = max_trajectory_points
        self.cleanup_timeout = cleanup_timeout

        # Trajectories: {track_id: VehicleTrajectory}
        # track_id format: string (5 ký tự alphanumeric + hhmmss)
        self.trajectories: Dict[str, VehicleTrajectory] = {}

        # Stats
        self._last_cleanup = datetime.now()
        self._cleanup_interval = 5  # Cleanup mỗi 5 giây

        logger.info(
            f"TrajectoryTracker initialized: camera={camera_id}, "
            f"max_points={max_trajectory_points}, timeout={cleanup_timeout}s"
        )

    def update(self, track_id: str, bbox: Tuple[float, float, float, float]):
        """
        Update trajectory với vị trí mới

        Args:
            track_id: ID của track
            bbox: Bounding box [x1, y1, x2, y2]
        """
        # Tính center point
        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2

        # Tạo trajectory mới nếu chưa có
        if track_id not in self.trajectories:
            self.trajectories[track_id] = VehicleTrajectory(
                track_id=track_id,
                max_points=self.max_trajectory_points
            )

        # Thêm point mới
        self.trajectories[track_id].add_point(center_x, center_y, bbox)

        # Cleanup định kỳ
        self._periodic_cleanup()

    def get_trajectory(self, track_id: str) -> Optional[VehicleTrajectory]:
        """Lấy trajectory của track"""
        return self.trajectories.get(track_id)

    def get_all_trajectories(self) -> Dict[str, VehicleTrajectory]:
        """Lấy tất cả trajectories đang track"""
        return self.trajectories.copy()

    def get_active_trajectories(self, seconds: float = 3.0) -> Dict[str, VehicleTrajectory]:
        """
        Lấy các trajectories còn active (có update gần đây)

        Args:
            seconds: Thời gian (giây) để coi là active
        """
        cutoff = datetime.now() - timedelta(seconds=seconds)
        return {
            track_id: traj
            for track_id, traj in self.trajectories.items()
            if traj.last_update >= cutoff
        }

    def _periodic_cleanup(self):
        """Cleanup trajectories cũ định kỳ"""
        now = datetime.now()

        # Chỉ cleanup theo interval
        if (now - self._last_cleanup).total_seconds() < self._cleanup_interval:
            return

        self._last_cleanup = now
        cutoff = now - timedelta(seconds=self.cleanup_timeout)

        # Tìm trajectories cần xóa
        to_remove = [
            track_id for track_id, traj in self.trajectories.items()
            if traj.last_update < cutoff
        ]

        # Xóa trajectories cũ
        for track_id in to_remove:
            del self.trajectories[track_id]

        if to_remove:
            logger.debug(f"Cleaned up {len(to_remove)} old trajectories")

    def clear(self):
        """Xóa tất cả trajectories"""
        self.trajectories.clear()
        logger.info(f"Cleared all trajectories for camera {self.camera_id}")

    def prune_inactive(self, max_age_seconds: float) -> None:
        """
        Loại bỏ các trajectory không được cập nhật trong khoảng thời gian cho trước.

        Args:
            max_age_seconds: Thời gian tối đa cho phép (giây). <=0 sẽ bỏ qua.
        """
        if max_age_seconds is None or max_age_seconds <= 0:
            return

        cutoff = datetime.now() - timedelta(seconds=max_age_seconds)
        to_remove = [
            track_id for track_id, traj in self.trajectories.items()
            if traj.last_update < cutoff
        ]
        if not to_remove:
            return

        for track_id in to_remove:
            self.trajectories.pop(track_id, None)
        logger.debug(f"Pruned {len(to_remove)} inactive trajectories (> {max_age_seconds:.2f}s)")


# Singleton per camera
_trackers: Dict[str, TrajectoryTracker] = {}


def get_trajectory_tracker(
    camera_id: str,
    max_trajectory_points: int = 30,
    cleanup_timeout: int = 30
) -> TrajectoryTracker:
    """
    Get or create TrajectoryTracker cho camera

    Args:
        camera_id: ID camera
        max_trajectory_points: Số điểm tối đa mỗi trajectory
        cleanup_timeout: Timeout để cleanup (giây)
    """
    if camera_id not in _trackers:
        _trackers[camera_id] = TrajectoryTracker(
            camera_id=camera_id,
            max_trajectory_points=max_trajectory_points,
            cleanup_timeout=cleanup_timeout
        )
    return _trackers[camera_id]
