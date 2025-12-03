"""
Stopline Crossing Detector - Ghi hình phương tiện vượt stopline
"""

import time
from typing import Dict, Tuple
from ...utils.logger import app_logger as logger
from ...config.config import settings


class StoplineCrossingDetector:
    """Theo dõi xe vượt stopline để ghi hình"""

    def __init__(self, camera_id: str):
        """
        Args:
            camera_id: ID camera
        """
        self.camera_id = camera_id
        self.detection_range = settings.STOPLINE_DETECTION_RANGE
        self.cleanup_timeout = settings.STOPLINE_CROSSING_TIMEOUT

        # Track state: {track_id: {"position": "above"/"below", "crossed": bool, "last_seen": timestamp}}
        # position: "above" = y2 < stopline_y (xe ở trên stopline), "below" = y2 >= stopline_y (xe ở dưới stopline)
        # track_id format: string (5 ký tự alphanumeric + hhmmss)
        self.tracks: Dict[str, Dict] = {}

        logger.info(f"StoplineCrossingDetector init: camera={camera_id}, range={self.detection_range}px")

    def check_crossing(self, track_id: str, bbox: Tuple[float, float, float, float], stopline_y: float) -> bool:
        """
        Check xe vượt stopline để ghi hình - REAL-TIME

        Logic:
        - y2 (tọa độ đáy bbox) >= và <= lineStop (nằm trong vùng STOPLINE_DETECTION_RANGE)
        - Vùng detection: stopline_y ± detection_range (tổng 2*detection_range, lineStop là trung tâm)
        - Ghi nhận NGAY khi xe vào vùng detection (không cần chờ chuyển trạng thái)
        - Mỗi track chỉ ghi 1 lần để tránh duplicate

        Returns:
            True nếu cần ghi hình (xe đang trong vùng detection range)
        """
        x1, y1, x2, y2 = bbox
        distance = y2 - stopline_y

        # Vùng detection: stopline_y ± detection_range (CẢ 2 PHÍA)
        # Ví dụ: stopline_y=480, range=60 → vùng=[420-540] (tổng 120px, stopline ở giữa)
        detection_min = stopline_y - self.detection_range
        detection_max = stopline_y + self.detection_range  # ← SỬA: Phát hiện CẢ 2 PHÍA
        is_in_range = detection_min <= y2 <= detection_max

        # Init track nếu chưa có
        if track_id not in self.tracks:
            self.tracks[track_id] = {
                "crossed": False,
                "last_seen": time.time()
            }
            logger.debug(f"🆕 Track {track_id} initialized: y2={y2:.1f}, stopline={stopline_y:.1f}, range=[{detection_min:.0f}-{detection_max:.0f}]")

        track_state = self.tracks[track_id]
        track_state["last_seen"] = time.time()

        # LOG chi tiết mỗi 5 lần để giảm log overhead (giữ real-time nhưng không spam)
        # Dùng hash để check modulo với string track_id
        track_id_for_log = hash(track_id) % 1000

        # Giảm log
        if is_in_range and not track_state.get('crossed', False):
            logger.debug(
                f"Track {track_id}: y2={y2:.1f}, stopline={stopline_y:.1f}, "
                f"range=[{detection_min:.0f}-{detection_max:.0f}]"
            )

        # ĐIỀU KIỆN PHÁT HIỆN: Xe trong vùng detection range (y2 >= và <= lineStop trong ±detection_range)
        # Ghi nhận NGAY khi thỏa điều kiện, không cần chờ chuyển trạng thái
        if is_in_range:
            # Đã ghi rồi → skip (tránh duplicate)
            if track_state["crossed"]:
                logger.debug(f"⏭️ Track {track_id} đã được ghi nhận trước đó, bỏ qua")
                return False

            track_state["crossed"] = True
            logger.info(f"✅ Stopline: {track_id}")
            return True

        return False

    def cleanup_old_tracks(self):
        """Xóa tracks cũ"""
        current_time = time.time()
        to_remove = [tid for tid, state in self.tracks.items()
                     if current_time - state["last_seen"] > self.cleanup_timeout]

        for track_id in to_remove:
            del self.tracks[track_id]


# Singleton per camera
_detectors: Dict[str, StoplineCrossingDetector] = {}


def get_stopline_crossing_detector(camera_id: str) -> StoplineCrossingDetector:
    """Get or create StoplineCrossingDetector cho camera"""
    if camera_id not in _detectors:
        _detectors[camera_id] = StoplineCrossingDetector(camera_id)
    return _detectors[camera_id]
