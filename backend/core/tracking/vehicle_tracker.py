"""
Object Tracking Service - ByteTrack Implementation
Gán ID cố định cho mỗi xe, track qua nhiều frames
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import random
import string
from collections import defaultdict
from datetime import datetime, timedelta

from ...utils.logger import app_logger as logger


class TrackState:
    """Trạng thái của track"""
    New = 0
    Tracked = 1
    Lost = 2
    Removed = 3


class Track:
    """
    Single object track

    Attributes:
        track_id: ID duy nhất của track
        bbox: [x1, y1, x2, y2]
        class_name: Loại xe (car, motorcycle, bus, truck)
        confidence: Độ tin cậy
        state: Trạng thái track (New/Tracked/Lost/Removed)
        hits: Số lần được match
        age: Số frame từ khi tạo
        time_since_update: Số frame từ lần update cuối
    """

    def __init__(
        self,
        bbox: List[float],
        class_name: str,
        confidence: float,
        frame_id: int,
        track_id: str,
        min_hits: int,
        init_grace_frames: int,
        max_age: int
    ):
        # Gán ID từ tracker (riêng cho mỗi camera)
        # track_id format: 5 số ngẫu nhiên + hhmmss (string)
        self.track_id = track_id
        self.bbox = bbox
        self.class_name = class_name
        self.confidence = confidence
        self.state = TrackState.New
        self.hits = 1
        self.age = 1
        self.time_since_update = 0
        self.frame_id = frame_id
        self.created_at = datetime.now()
        self.min_hits = max(1, min_hits)
        self.init_grace_frames = max(1, init_grace_frames)
        self.max_age = max(1, max_age)

    def update(self, bbox: List[float], class_name: str, confidence: float, frame_id: int):
        """Update track với detection mới"""
        self.bbox = bbox
        self.class_name = class_name
        self.confidence = confidence
        self.hits += 1
        self.time_since_update = 0
        self.frame_id = frame_id

        if self.state == TrackState.New and self.hits >= self.min_hits:
            self.state = TrackState.Tracked
        elif self.state == TrackState.Lost and self.hits >= self.min_hits:
            self.state = TrackState.Tracked

    def mark_missed(self):
        """Đánh dấu track bị miss trong frame này"""
        self.time_since_update += 1
        if self.state == TrackState.New:
            # Cho phép track mới bỏ lỡ một vài frame trước khi loại bỏ
            if self.time_since_update >= self.init_grace_frames:
                self.state = TrackState.Lost
        elif self.state == TrackState.Tracked and self.time_since_update >= self.init_grace_frames:
            self.state = TrackState.Lost

        if self.time_since_update > self.max_age:
            self.state = TrackState.Removed

    def get_center(self) -> Tuple[float, float]:
        """Lấy tọa độ center của bbox"""
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    def is_active(self) -> bool:
        """Check track có active không"""
        return self.state in [TrackState.New, TrackState.Tracked]


class ObjectTracker:
    """
    ByteTrack-inspired object tracker

    Sử dụng IoU matching để track objects qua frames

    Config:
        - iou_threshold: Ngưỡng IoU để match (default 0.3)
        - max_age: Số frame tối đa giữ track lost (default 30)
        - min_hits: Số hits tối thiểu để confirm track (default 3)
    """

    def __init__(
        self,
        iou_threshold: float = 0.3,
        max_age: int = 30,
        min_hits: int = 3,
        center_distance_threshold: float = 120.0,
        init_grace_frames: int = 3
    ):
        self.iou_threshold = iou_threshold
        self.max_age = max_age
        self.min_hits = min_hits
        self.center_distance_threshold = center_distance_threshold
        self.init_grace_frames = max(1, init_grace_frames)

        self.tracks: List[Track] = []
        self.frame_count = 0
        # Không dùng counter nữa - track_id sẽ là string: 5 số ngẫu nhiên + hhmmss

    def update(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Update tracker với detections từ frame mới

        Args:
            detections: List của {bbox, class_name, confidence}

        Returns:
            List của detections với track_id được gán
        """
        self.frame_count += 1

        # TODO: BƯỚC 1: Chia detections theo confidence  (ByteTrack strategy)
        high_conf_dets = []
        low_conf_dets = []

        for det in detections:
            if det['confidence'] >= 0.5:
                high_conf_dets.append(det)
            else:
                low_conf_dets.append(det)

        # TODO: B2: Match high confidence detections với active tracks
        matched_tracks, unmatched_tracks, unmatched_dets = self._match(
            self.tracks, high_conf_dets
        )

        # Update matched tracks
        for track_idx, det_idx in matched_tracks:
            det = high_conf_dets[det_idx]
            self.tracks[track_idx].update(
                det['bbox'], det['class_name'], det['confidence'], self.frame_count
            )

        # TODO: BƯỚC 3: Match low confidence với unmatched tracks
        unmatched_low_det_indices = set(range(len(low_conf_dets)))
        if len(low_conf_dets) > 0 and len(unmatched_tracks) > 0:
            remaining_tracks = [self.tracks[i] for i in unmatched_tracks]
            matched_tracks2, unmatched_tracks2, matched_low_det = self._match(
                remaining_tracks, low_conf_dets
            )

            # Track các index đã matched để remove sau
            matched_indices = set()
            for track_idx, det_idx in matched_tracks2:
                det = low_conf_dets[det_idx]
                # track_idx là index trong remaining_tracks
                # Map về original track index
                original_track_idx = unmatched_tracks[track_idx]
                self.tracks[original_track_idx].update(
                    det['bbox'], det['class_name'], det['confidence'], self.frame_count
                )
                matched_indices.add(track_idx)
                if det_idx in unmatched_low_det_indices:
                    unmatched_low_det_indices.remove(det_idx)

            # Remove matched tracks từ unmatched_tracks
            unmatched_tracks = [idx for i, idx in enumerate(unmatched_tracks) if i not in matched_indices]

        # TODO: B4: Đánh dấu track bị miss
        for track_idx in unmatched_tracks:
            self.tracks[track_idx].mark_missed()

        # TODO: B5 Create new tracks
        for det_idx in unmatched_dets:
            det = high_conf_dets[det_idx]
            track_id = self._generate_track_id()
            new_track = Track(
                det['bbox'],
                det['class_name'],
                det['confidence'],
                self.frame_count,
                track_id,
                self.min_hits,
                self.init_grace_frames,
                self.max_age
            )
            self.tracks.append(new_track)

        # Create new tracks cho unmatched LOW-confidence detections để đảm bảo luôn có track_id
        # (đáp ứng yêu cầu gán ID ngay khi phát hiện)
        for det_idx in sorted(list(unmatched_low_det_indices)):
            det = low_conf_dets[det_idx]
            track_id = self._generate_track_id()
            new_track = Track(
                det['bbox'],
                det['class_name'],
                det['confidence'],
                self.frame_count,
                track_id,
                self.min_hits,
                self.init_grace_frames,
                self.max_age
            )
            self.tracks.append(new_track)

        # Remove dead tracks
        self.tracks = [t for t in self.tracks if t.state != TrackState.Removed]

        # Assign track IDs to detections
        # Đảm bảo mọi detection trong vehicles_to_track đều có track_id
        tracked_detections = []
        for det in detections:
            # Tìm track tương ứng từ matched/unmatched đã xử lý ở trên
            best_track = None
            best_iou = 0.0
            best_distance = float("inf")

            for track in self.tracks:
                if not track.is_active():
                    continue
                iou = self._calculate_iou(det['bbox'], track.bbox)
                distance = self._calculate_center_distance(det['bbox'], track.bbox)

                if iou > best_iou or (iou == best_iou and distance < best_distance):
                    best_iou = iou
                    best_track = track
                    best_distance = distance

            # Add track_id to detection
            det_copy = det.copy()
            can_keep_track = (
                best_track
                and (
                    best_iou > self.iou_threshold
                    or best_distance <= self.center_distance_threshold
                )
            )

            if can_keep_track:
                if best_iou <= self.iou_threshold:
                    best_track.update(
                        det['bbox'],
                        det['class_name'],
                        det['confidence'],
                        self.frame_count
                    )
                det_copy['track_id'] = best_track.track_id
            elif 'track_id' in det and det['track_id'] is not None:
                # Giữ nguyên track_id nếu đã được gán từ matching
                det_copy['track_id'] = det['track_id']
            else:
                # Nếu không match được, tạo track mới cho detection này
                # (điều này đảm bảo mọi vehicle đều có track_id)
                track_id = self._generate_track_id()
                new_track = Track(
                    det['bbox'],
                    det['class_name'],
                    det['confidence'],
                    self.frame_count,
                    track_id,
                    self.min_hits,
                    self.init_grace_frames,
                    self.max_age
                )
                self.tracks.append(new_track)
                det_copy['track_id'] = track_id
                logger.debug(
                    f"🆕 Tạo track mới {track_id} cho detection không match (IoU={best_iou:.2f}, distance={best_distance:.1f})"
                )

            tracked_detections.append(det_copy)

        return tracked_detections

    def _match(
        self,
        tracks: List[Track],
        detections: List[Dict[str, Any]]
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """
        Match tracks với detections using IoU

        Returns:
            matched: List of (track_idx, detection_idx)
            unmatched_tracks: List of track indices
            unmatched_detections: List of detection indices
        """
        if len(tracks) == 0 or len(detections) == 0:
            return [], list(range(len(tracks))), list(range(len(detections)))

        # Calculate IoU matrix
        iou_matrix = np.zeros((len(tracks), len(detections)))
        for t_idx, track in enumerate(tracks):
            for d_idx, det in enumerate(detections):
                iou_matrix[t_idx, d_idx] = self._calculate_iou(track.bbox, det['bbox'])

        # Greedy matching
        matched = []
        unmatched_tracks = list(range(len(tracks)))
        unmatched_dets = list(range(len(detections)))

        while iou_matrix.size > 0 and iou_matrix.max() > self.iou_threshold:
            # Find best match
            max_idx = np.unravel_index(iou_matrix.argmax(), iou_matrix.shape)
            t_idx, d_idx = max_idx

            # Add to matched
            matched.append((unmatched_tracks[t_idx], unmatched_dets[d_idx]))

            # Remove from unmatched
            unmatched_tracks.pop(t_idx)
            unmatched_dets.pop(d_idx)

            # Remove row and column
            iou_matrix = np.delete(iou_matrix, t_idx, axis=0)
            iou_matrix = np.delete(iou_matrix, d_idx, axis=1)

        return matched, unmatched_tracks, unmatched_dets

    def _calculate_iou(self, bbox1: List[float], bbox2: List[float]) -> float:
        """Calculate IoU between 2 bboxes"""
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2

        # Intersection
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)

        if x2_i < x1_i or y2_i < y1_i:
            return 0.0

        inter_area = (x2_i - x1_i) * (y2_i - y1_i)

        # Union
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union_area = area1 + area2 - inter_area

        return inter_area / union_area if union_area > 0 else 0.0

    def _calculate_center_distance(self, bbox1: List[float], bbox2: List[float]) -> float:
        """Khoảng cách giữa tâm 2 bbox"""
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2

        cx1 = (x1_1 + x2_1) / 2
        cy1 = (y1_1 + y2_1) / 2
        cx2 = (x1_2 + x2_2) / 2
        cy2 = (y1_2 + y2_2) / 2

        return ((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2) ** 0.5

    def get_active_tracks(self) -> List[Track]:
        """Lấy tất cả tracks đang active"""
        return [t for t in self.tracks if t.is_active()]

    def get_track_count(self) -> int:
        """Đếm số tracks đang active"""
        return len(self.get_active_tracks())

    def _generate_track_id(self) -> str:
        """
        Tạo track_id dạng: 5 ký tự alphanumeric ngẫu nhiên + hhmmss
        Chỉ dùng chữ cái (a-z, A-Z) và số (0-9), không có ký tự đặc biệt

        Returns:
            track_id string: Ví dụ "2h6005200" (3 ký tự ngẫu nhiên + 005200 = 00:52:00)
        """
        # 5 ký tự alphanumeric ngẫu nhiên (số + chữ cái hoa/thường)
        # Chỉ dùng: 0-9, a-z, A-Z (không có ký tự đặc biệt)
        chars = string.digits + string.ascii_letters  # digits + ascii_lowercase + ascii_uppercase
        random_part = ''.join(random.choice(chars) for _ in range(3))

        # hhmmss từ thời gian hiện tại (6 số)
        now = datetime.now()
        time_part = now.strftime("%H%M%S")  # HHMMSS format

        track_id = f"{random_part}{time_part}"
        return track_id

    def reset(self):
        """Reset tracker"""
        self.tracks = []
        self.frame_count = 0


# Global trackers cho mỗi camera
_camera_trackers: Dict[str, ObjectTracker] = {}


def get_tracker(camera_id: str, **kwargs) -> ObjectTracker:
    """
    Get or create tracker cho camera

    Args:
        camera_id: ID camera
        **kwargs: Config cho tracker (iou_threshold, max_age, min_hits)
    """
    if camera_id not in _camera_trackers:
        _camera_trackers[camera_id] = ObjectTracker(**kwargs)
    return _camera_trackers[camera_id]


def reset_tracker(camera_id: str):
    """Reset tracker cho camera"""
    if camera_id in _camera_trackers:
        _camera_trackers[camera_id].reset()
        del _camera_trackers[camera_id]
