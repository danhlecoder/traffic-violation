"""
Trajectory Drawer - Vẽ quỹ đạo di chuyển lên frame

Chức năng:
- Vẽ trajectory của vehicles lên video frame
- Hiển thị hướng di chuyển với mũi tên
- Gradient color theo thời gian (điểm cũ → mờ dần)
- Hiển thị track_id và thông tin tốc độ
"""

import cv2
import numpy as np
from typing import Dict, Tuple, Optional

from .trajectory_tracker import VehicleTrajectory, TrajectoryTracker


class TrajectoryDrawer:
    """Vẽ trajectory lên frame"""

    def __init__(
        self,
        line_thickness: int = 2,
        point_radius: int = 3,
        arrow_length: int = 30,
        show_speed: bool = True,
        show_track_id: bool = True,
        fade_effect: bool = True,
        speed_in_kmh: bool = True,
        pixels_per_meter: float = 20.0
    ):
        """
        Args:
            line_thickness: Độ dày đường trajectory
            point_radius: Bán kính điểm trên trajectory
            arrow_length: Độ dài mũi tên chỉ hướng
            show_speed: Hiển thị tốc độ ước tính
            show_track_id: Hiển thị track_id
            fade_effect: Dùng fade effect (điểm cũ mờ dần)
            speed_in_kmh: Hiển thị tốc độ km/h (nếu False: px/s)
            pixels_per_meter: Calibration ratio (pixels/meter)
        """
        self.line_thickness = line_thickness
        self.point_radius = point_radius
        self.arrow_length = arrow_length
        self.show_speed = show_speed
        self.show_track_id = show_track_id
        self.fade_effect = fade_effect
        self.speed_in_kmh = speed_in_kmh
        self.pixels_per_meter = pixels_per_meter

        # Color palette (BGR format)
        self.colors = [
            (255, 0, 0),    # Blue
            (0, 255, 0),    # Green
            (0, 0, 255),    # Red
            (255, 255, 0),  # Cyan
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Yellow
            (128, 0, 128),  # Purple
            (255, 128, 0),  # Orange
        ]

    def get_color_for_track(self, track_id: str) -> Tuple[int, int, int]:
        """Lấy màu cho track_id (consistent color)"""
        # Dùng hash để có số cố định cho mỗi string
        idx = hash(track_id) % len(self.colors)
        return self.colors[idx]

    def draw_trajectory(
        self,
        frame: np.ndarray,
        trajectory: VehicleTrajectory,
        color: Optional[Tuple[int, int, int]] = None,
        stopline_y: Optional[float] = None,
        pixels_per_meter: Optional[float] = None
    ) -> np.ndarray:
        """
        Vẽ trajectory của 1 vehicle lên frame

        Args:
            frame: Video frame
            trajectory: VehicleTrajectory object
            color: Màu vẽ (nếu None sẽ dùng màu theo track_id)

        Returns:
            Frame với trajectory đã vẽ
        """
        points = trajectory.get_points()
        if not points:
            return frame

        # Chọn màu
        if color is None:
            color = self.get_color_for_track(trajectory.track_id)

        # Vẽ đường nối các điểm
        for i in range(1, len(points)):
            pt1 = points[i-1]
            pt2 = points[i]

            # Tính alpha (fade effect)
            if self.fade_effect:
                # Điểm cũ mờ hơn điểm mới
                alpha = i / len(points)
                draw_color = tuple(int(c * alpha) for c in color)
            else:
                draw_color = color

            # Vẽ line
            cv2.line(
                frame,
                (int(pt1.x), int(pt1.y)),
                (int(pt2.x), int(pt2.y)),
                draw_color,
                self.line_thickness,
                cv2.LINE_AA
            )

        # Vẽ các điểm
        for i, point in enumerate(points):
            # Tính alpha
            if self.fade_effect:
                alpha = (i + 1) / len(points)
                draw_color = tuple(int(c * alpha) for c in color)
            else:
                draw_color = color

            cv2.circle(
                frame,
                (int(point.x), int(point.y)),
                self.point_radius,
                draw_color,
                -1,
                cv2.LINE_AA
            )

        # Vẽ mũi tên chỉ hướng (tại điểm cuối)
        direction = trajectory.get_direction_vector()
        if direction is not None:
            last_point = points[-1]
            dx, dy = direction

            # Normalize và scale
            magnitude = (dx**2 + dy**2)**0.5
            if magnitude > 0:
                dx = dx / magnitude * self.arrow_length
                dy = dy / magnitude * self.arrow_length

                # Vẽ mũi tên
                arrow_end = (
                    int(last_point.x + dx),
                    int(last_point.y + dy)
                )
                cv2.arrowedLine(
                    frame,
                    (int(last_point.x), int(last_point.y)),
                    arrow_end,
                    color,
                    self.line_thickness,
                    cv2.LINE_AA,
                    tipLength=0.3
                )

        return frame

    def draw_all_trajectories(
        self,
        frame: np.ndarray,
        tracker: TrajectoryTracker,
        active_only: bool = True,
        active_seconds: float = 3.0,
        stopline_y: Optional[float] = None,
        pixels_per_meter: Optional[float] = None
    ) -> np.ndarray:
        """
        Vẽ tất cả trajectories lên frame

        Args:
            frame: Video frame
            tracker: TrajectoryTracker instance
            active_only: Chỉ vẽ trajectories đang active
            active_seconds: Thời gian (giây) để coi là active

        Returns:
            Frame với trajectories đã vẽ
        """
        # Lấy trajectories cần vẽ
        if active_only:
            trajectories = tracker.get_active_trajectories(active_seconds)
        else:
            trajectories = tracker.get_all_trajectories()

        # Vẽ từng trajectory
        for trajectory in trajectories.values():
            frame = self.draw_trajectory(
                frame,
                trajectory,
                stopline_y=stopline_y,
                pixels_per_meter=pixels_per_meter,
            )

        return frame

    def draw_trajectory_stats(
        self,
        frame: np.ndarray,
        tracker: TrajectoryTracker,
        position: Tuple[int, int] = (10, 90)
    ) -> np.ndarray:
        """
        Vẽ thống kê trajectories lên góc frame

        Args:
            frame: Video frame
            tracker: TrajectoryTracker instance
            position: Vị trí (x, y) để vẽ

        Returns:
            Frame với stats đã vẽ
        """
        x, y = position

        total = len(tracker.trajectories)
        active = len(tracker.get_active_trajectories())

        text = f"Trajectories: {active}/{total}"

        # Vẽ text với background
        cv2.putText(
            frame,
            text,
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

        return frame


# Singleton drawer
_drawer_instance: Optional[TrajectoryDrawer] = None


def get_trajectory_drawer(
    line_thickness: int = 2,
    point_radius: int = 3,
    arrow_length: int = 30,
    show_speed: bool = True,
    show_track_id: bool = True,
    fade_effect: bool = True,
    speed_in_kmh: bool = True,
    pixels_per_meter: float = 20.0
) -> TrajectoryDrawer:
    """
    Get or create TrajectoryDrawer instance
    """
    global _drawer_instance
    if _drawer_instance is None:
        _drawer_instance = TrajectoryDrawer(
            line_thickness=line_thickness,
            point_radius=point_radius,
            arrow_length=arrow_length,
            show_speed=show_speed,
            show_track_id=show_track_id,
            fade_effect=fade_effect,
            speed_in_kmh=speed_in_kmh,
            pixels_per_meter=pixels_per_meter
        )
    return _drawer_instance
