"""
Frame Processor - Xử lý và validate frame
Tách logic xử lý frame ra khỏi mjpeg.py để tái sử dụng
"""

import cv2
import numpy as np
from typing import Optional, Tuple
from ...utils.logger import stream_logger as logger


def validate_frame(frame: Optional[np.ndarray]) -> Tuple[bool, Optional[Tuple[int, int]]]:
    """
    Validate frame có hợp lệ không

    Args:
        frame: Frame cần validate

    Returns:
        (is_valid, dimensions): (True/False, (height, width) hoặc None)
    """
    if frame is None or frame.size == 0:
        return False, None

    try:
        h, w = frame.shape[:2]
        if h <= 0 or w <= 0:
            logger.warning(f"Frame có kích thước invalid: {w}x{h}")
            return False, None

        # Kiểm tra frame có pixel values hợp lệ
        mean_val = frame.mean()
        if mean_val < 5 or mean_val > 250:
            return False, None

        return True, (h, w)

    except Exception as e:
        logger.warning(f"Lỗi khi validate frame: {e}")
        return False, None


def prepare_detection_frame(frame: np.ndarray, detection_width: int) -> Tuple[np.ndarray, float]:
    """
    Chuẩn bị frame cho detection (resize nếu cần)

    Args:
        frame: Frame gốc
        detection_width: Chiều rộng mục tiêu (0 = không resize)

    Returns:
        (det_frame, scale_back): Frame đã resize và tỉ lệ scale về frame gốc
    """
    if detection_width <= 0:
        return frame, 1.0

    h, w = frame.shape[:2]
    if w <= detection_width:
        return frame, 1.0

    scale = detection_width / w
    new_h = int(h * scale)
    det_frame = cv2.resize(frame, (detection_width, new_h), interpolation=cv2.INTER_LINEAR)
    scale_back = w / detection_width

    return det_frame, scale_back


def scale_bboxes_back(detections: list, scale: float) -> None:
    """
    Scale bboxes về kích thước frame gốc (in-place)

    Args:
        detections: List detections với bbox
        scale: Tỉ lệ scale về frame gốc
    """
    if scale == 1.0:
        return

    for det in detections:
        if "bbox" in det:
            det["bbox"] = [coord * scale for coord in det["bbox"]]







