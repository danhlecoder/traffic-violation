"""
Image Processing Utilities - Xử lý ảnh cơ bản
"""

from typing import Tuple
import numpy as np


Point = Tuple[float, float]


def normalize_point(pt: Point, width: int, height: int) -> Point:
    """
    Chuẩn hóa tọa độ pixel về khoảng [0..1]
    
    Args:
        pt: Điểm (x, y) dạng pixel
        width: Chiều rộng ảnh
        height: Chiều cao ảnh
    
    Returns:
        Điểm (x, y) đã chuẩn hóa
    """
    x, y = pt
    if width <= 0 or height <= 0:
        return 0.0, 0.0
    return x / width, y / height


def extend_line_to_frame(
    x1: float, y1: float,
    x2: float, y2: float,
    w: int, h: int
) -> Tuple[float, float, float, float]:
    """
    Kéo dài đoạn thẳng tới biên khung hình
    
    Args:
        x1, y1: Điểm đầu
        x2, y2: Điểm cuối
        w: Chiều rộng ảnh
        h: Chiều cao ảnh
    
    Returns:
        (ex1, ey1, ex2, ey2): Tọa độ đã kéo dài
    """
    dx, dy = x2 - x1, y2 - y1
    
    if abs(dx) >= abs(dy):
        # Phương ngang: kéo tới biên trái/phải
        denom = dx if dx != 0 else 1e-6
        
        t1 = (0 - x1) / denom
        ey1 = y1 + t1 * dy
        
        t2 = ((w - 1) - x1) / denom
        ey2 = y1 + t2 * dy
        
        return 0.0, ey1, float(w - 1), ey2
    else:
        # Phương dọc: kéo tới biên trên/dưới
        denom = dy if dy != 0 else 1e-6
        
        t1 = (0 - y1) / denom
        ex1 = x1 + t1 * dx
        
        t2 = ((h - 1) - y1) / denom
        ex2 = x1 + t2 * dx
        
        return ex1, 0.0, ex2, float(h - 1)


def center_crop_to_16_9(frame_bgr: np.ndarray) -> np.ndarray:
    """
    Cắt giữa khung hình về tỉ lệ 16:9 (không kéo giãn)
    
    Args:
        frame_bgr: Frame ảnh BGR
    
    Returns:
        Frame đã crop về 16:9
    """
    if frame_bgr is None or frame_bgr.size == 0:
        return frame_bgr
    
    h, w = frame_bgr.shape[:2]
    if h == 0 or w == 0:
        return frame_bgr
    
    target_ratio = 16.0 / 9.0
    current_ratio = float(w) / float(h)
    
    if abs(current_ratio - target_ratio) < 1e-3:
        return frame_bgr
    
    if current_ratio > target_ratio:
        # Quá rộng: cắt bớt chiều ngang
        new_w = int(round(h * target_ratio))
        x0 = max(0, (w - new_w) // 2)
        x1 = min(w, x0 + new_w)
        return frame_bgr[:, x0:x1]
    else:
        # Quá cao: cắt bớt chiều dọc
        new_h = int(round(w / target_ratio))
        y0 = max(0, (h - new_h) // 2)
        y1 = min(h, y0 + new_h)
        return frame_bgr[y0:y1, :]
