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
        self.threshold = settings.STOPLINE_CROSSING_THRESHOLD
        self.detection_range = settings.STOPLINE_DETECTION_RANGE
        self.cleanup_timeout = settings.STOPLINE_CROSSING_TIMEOUT
        
        # Track state: {track_id: {"crossed": bool, "last_seen": timestamp}}
        self.tracks: Dict[int, Dict] = {}
        
        logger.info(f"StoplineCrossingDetector init: camera={camera_id}, threshold={self.threshold}px, range={self.detection_range}px")
    
    def check_crossing(self, track_id: int, bbox: Tuple[float, float, float, float], stopline_y: float) -> bool:
        """
        Check xe vượt stopline để ghi hình
        
        Logic:
        - y2 >= stopline_y: xe đã vượt
        - abs(y2 - stopline_y) <= detection_range: trong vùng ghi hình
        - Mỗi track chỉ ghi 1 lần
        
        Returns:
            True nếu cần ghi hình (lần đầu vượt)
        """
        _, _, _, y2 = bbox
        
        # Init track
        if track_id not in self.tracks:
            self.tracks[track_id] = {"crossed": False, "last_seen": time.time()}
        
        self.tracks[track_id]["last_seen"] = time.time()
        
        # Đã ghi rồi → skip
        if self.tracks[track_id]["crossed"]:
            return False
        
        distance = y2 - stopline_y
        
        # Check: y2 >= stopline VÀ trong vùng detection_range
        if y2 >= stopline_y and abs(distance) <= self.detection_range:
            self.tracks[track_id]["crossed"] = True
            logger.info(f"📹 [Stopline Crossing] Track {track_id}: y2={y2:.1f}px, stopline={stopline_y:.1f}px, distance={distance:.1f}px")
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
