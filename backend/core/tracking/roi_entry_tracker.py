"""
ROI State Tracker - Track entry/exit events for violations

Chỉ trigger violation khi xe VÀO ROI (OUTSIDE → INSIDE)
Tránh duplicate bằng cách track state của mỗi track_id
"""

from typing import Dict, Optional, Set
from datetime import datetime, timedelta
from enum import Enum

from ...utils.logger import app_logger as logger


class ROIState(Enum):
    """Trạng thái của track so với ROI"""
    OUTSIDE = "outside"  # Ngoài ROI
    INSIDE = "inside"    # Trong ROI
    UNKNOWN = "unknown"  # Chưa xác định


class TrackROIState:
    """State của 1 track trong ROI"""
    
    def __init__(self, track_id: int):
        self.track_id = track_id
        self.state = ROIState.UNKNOWN
        self.last_update = datetime.now()
        self.entry_time: Optional[datetime] = None
        self.violation_created = False
    
    def update(self, is_in_roi: bool) -> bool:
        """
        Update state và return True nếu là ENTRY event
        
        Args:
            is_in_roi: Track có trong ROI không
            
        Returns:
            True nếu đây là entry event (OUTSIDE → INSIDE hoặc UNKNOWN → INSIDE)
        """
        self.last_update = datetime.now()
        
        # Determine new state
        new_state = ROIState.INSIDE if is_in_roi else ROIState.OUTSIDE
        
        # Check for entry event
        # Case 1: Normal entry (OUTSIDE → INSIDE)
        # Case 2: First appearance in ROI (UNKNOWN → INSIDE) - cho trường hợp không có ROI config
        is_entry = (
            (self.state == ROIState.OUTSIDE and new_state == ROIState.INSIDE) or
            (self.state == ROIState.UNKNOWN and new_state == ROIState.INSIDE)
        )
        
        # Update state
        old_state = self.state
        self.state = new_state
        
        # Track entry time
        if is_entry:
            self.entry_time = datetime.now()
            self.violation_created = False
        
        return is_entry
    
    def should_create_violation(self) -> bool:
        """Check xem có nên tạo violation không"""
        return (
            self.state == ROIState.INSIDE and 
            not self.violation_created
        )
    
    def mark_violation_created(self):
        """Đánh dấu đã tạo violation"""
        self.violation_created = True


class ROIStateTracker:
    """
    Track entry/exit state của tất cả vehicles
    
    Features:
    - Chỉ trigger violation khi entry (OUTSIDE → INSIDE)
    - Mỗi track chỉ tạo 1 violation duy nhất
    - Auto cleanup stale tracks
    
    Config:
    - cleanup_timeout: Thời gian (giây) để cleanup tracks cũ
    """
    
    def __init__(self, cleanup_timeout: int = 60):
        """
        Args:
            cleanup_timeout: Cleanup tracks không update trong X giây
        """
        self.cleanup_timeout = cleanup_timeout
        self.tracks: Dict[int, TrackROIState] = {}
        self._last_cleanup = datetime.now()
    
    def update(self, track_id: int, is_in_roi: bool) -> bool:
        """
        Update track state
        
        Args:
            track_id: Track ID từ object tracker
            is_in_roi: Track có trong ROI không
            
        Returns:
            True nếu là entry event (cần tạo violation)
        """
        # Get or create track state
        if track_id not in self.tracks:
            self.tracks[track_id] = TrackROIState(track_id)
        
        track_state = self.tracks[track_id]
        
        # Update và check entry
        is_entry = track_state.update(is_in_roi)
        
        # Periodic cleanup
        self._maybe_cleanup()
        
        return is_entry
    
    def should_create_violation(self, track_id: int) -> bool:
        """
        Check xem track này có cần tạo violation không
        
        Args:
            track_id: Track ID
            
        Returns:
            True nếu cần tạo violation
        """
        if track_id not in self.tracks:
            return False
        
        track_state = self.tracks[track_id]
        return track_state.should_create_violation()
    
    def mark_violation_created(self, track_id: int):
        """Đánh dấu đã tạo violation cho track"""
        if track_id in self.tracks:
            self.tracks[track_id].mark_violation_created()
    
    def get_state(self, track_id: int) -> Optional[ROIState]:
        """Lấy state hiện tại của track"""
        if track_id in self.tracks:
            return self.tracks[track_id].state
        return None
    
    def _maybe_cleanup(self):
        """Cleanup tracks cũ (gọi định kỳ)"""
        now = datetime.now()
        
        # Chỉ cleanup mỗi 10s
        if (now - self._last_cleanup).total_seconds() < 10:
            return
        
        self._last_cleanup = now
        cutoff = now - timedelta(seconds=self.cleanup_timeout)
        
        # Remove stale tracks
        stale_tracks = [
            tid for tid, track in self.tracks.items()
            if track.last_update < cutoff
        ]
        
        for tid in stale_tracks:
            del self.tracks[tid]
        
        if stale_tracks:
            logger.debug(f"Cleaned up {len(stale_tracks)} stale ROI tracks")
    
    def get_stats(self) -> Dict[str, int]:
        """Lấy thống kê"""
        inside = sum(1 for t in self.tracks.values() if t.state == ROIState.INSIDE)
        outside = sum(1 for t in self.tracks.values() if t.state == ROIState.OUTSIDE)
        
        return {
            "total_tracks": len(self.tracks),
            "inside_roi": inside,
            "outside_roi": outside,
            "violations_created": sum(1 for t in self.tracks.values() if t.violation_created)
        }
    
    def reset(self):
        """Reset tất cả tracks"""
        self.tracks.clear()


# Global ROI state trackers cho mỗi camera
_roi_state_trackers: Dict[str, ROIStateTracker] = {}


def get_roi_state_tracker(camera_id: str, cleanup_timeout: int = 60) -> ROIStateTracker:
    """
    Get or create ROI state tracker cho camera
    
    Args:
        camera_id: Camera ID
        cleanup_timeout: Cleanup timeout (seconds)
    """
    if camera_id not in _roi_state_trackers:
        _roi_state_trackers[camera_id] = ROIStateTracker(cleanup_timeout)
    return _roi_state_trackers[camera_id]


def reset_roi_state_tracker(camera_id: str):
    """Reset ROI state tracker cho camera"""
    if camera_id in _roi_state_trackers:
        _roi_state_trackers[camera_id].reset()
        del _roi_state_trackers[camera_id]
