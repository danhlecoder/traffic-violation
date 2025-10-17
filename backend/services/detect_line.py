"""
Computer Vision Service - Stop Line Detection

Chức năng:
- Phát hiện vạch dừng từ ảnh camera (Canny + HoughLinesP)
- Crop ảnh về tỉ lệ 16:9
- Chuẩn hóa tọa độ về [0,1]
"""

import math
from typing import Optional, Tuple
import cv2
import numpy as np

from ..core.config import settings
from ..utils.logger import app_logger as logger


Point = Tuple[float, float]
Segment = Tuple[Point, Point]


def _normalize_point(pt: Point, width: int, height: int) -> Point:
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


def _extend_line_to_frame(
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

        # Giao điểm với x=0
        t1 = (0 - x1) / denom
        ey1 = y1 + t1 * dy

        # Giao điểm với x=w-1
        t2 = ((w - 1) - x1) / denom
        ey2 = y1 + t2 * dy

        return 0.0, ey1, float(w - 1), ey2
    else:
        # Phương dọc: kéo tới biên trên/dưới
        denom = dy if dy != 0 else 1e-6

        # Giao điểm với y=0
        t1 = (0 - y1) / denom
        ex1 = x1 + t1 * dx

        # Giao điểm với y=h-1
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

    # Đã đúng tỉ lệ rồi
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


def detect_stop_line_points(frame_bgr: np.ndarray) -> Optional[Segment]:
    """
    Phát hiện vạch dừng và trả về 2 điểm pixel (đã kéo dài tới biên)

    Quy trình:
    1. Chuyển xám -> Gaussian blur -> Canny edge
    2. HoughLinesP tìm các đoạn thẳng
    3. Lọc các đoạn gần ngang, gần tâm, nửa dưới ảnh
    4. Chọn đoạn có avg_y lớn nhất (gần đáy nhất)
    5. Kéo dài tới biên khung hình

    Args:
        frame_bgr: Frame ảnh BGR

    Returns:
        Tuple 2 điểm (x1,y1), (x2,y2) hoặc None nếu không tìm thấy
    """
    if frame_bgr is None or frame_bgr.size == 0:
        return None

    img_h, img_w = frame_bgr.shape[:2]
    if img_h <= 0 or img_w <= 0:
        return None

    try:
        # 1. Tiền xử lý
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        edges = cv2.Canny(blur, settings.VISION_CANNY_LOW, settings.VISION_CANNY_HIGH)

        # 2. Tìm đoạn thẳng
        min_len = max(settings.VISION_MIN_LINE_LEN_MIN_PX, int(img_w * settings.VISION_MIN_LINE_LEN_FACTOR))
        max_gap = max(settings.VISION_MAX_GAP_MIN_PX, int(img_w * settings.VISION_MAX_GAP_FACTOR))

        lines = cv2.HoughLinesP(
            edges,
            rho=settings.VISION_HOUGH_RHO,
            theta=settings.VISION_HOUGH_THETA,
            threshold=settings.VISION_HOUGH_THRESHOLD,
            minLineLength=min_len,
            maxLineGap=max_gap,
        )

        if lines is None or len(lines) == 0:
            return None

        # 3. Lọc và chọn đoạn tốt nhất
        best_line: Optional[Tuple[float, float, float, float]] = None
        best_avg_y = -1.0
        center_x = img_w / 2.0

        for line in lines:
            x1, y1, x2, y2 = [float(v) for v in line[0]]
            dx, dy = (x2 - x1), (y2 - y1)

            # Kiểm tra góc (gần ngang)
            angle = abs(math.degrees(math.atan2(dy, dx)))
            if angle >= settings.VISION_ANGLE_MAX_DEG:
                continue

            avg_y = (y1 + y2) / 2.0
            avg_x = (x1 + x2) / 2.0

            # Kiểm tra gần tâm và nửa dưới
            near_center = abs(avg_x - center_x) < (img_w * settings.VISION_CENTER_BIAS_RATIO)
            near_bottom = avg_y > (img_h * settings.VISION_BOTTOM_MIN_Y_RATIO)

            if near_center and near_bottom and avg_y > best_avg_y:
                best_avg_y = avg_y
                best_line = (x1, y1, x2, y2)

        if best_line is None:
            return None

        # 4. Kéo dài tới biên
        ex1, ey1, ex2, ey2 = _extend_line_to_frame(*best_line, img_w, img_h)
        return (ex1, ey1), (ex2, ey2)

    except Exception as e:
        logger.error(f"Lỗi khi phát hiện vạch dừng: {e}")
        return None


def detect_stop_line_normalized(frame_bgr: np.ndarray) -> Optional[Segment]:
    """
    Phát hiện vạch dừng và trả về 2 điểm chuẩn hóa [0..1]

    Args:
        frame_bgr: Frame ảnh BGR

    Returns:
        Tuple 2 điểm chuẩn hóa hoặc None
    """
    result = detect_stop_line_points(frame_bgr)

    if result is None:
        return None

    (x1, y1), (x2, y2) = result
    h, w = frame_bgr.shape[:2]

    p1_norm = _normalize_point((x1, y1), w, h)
    p2_norm = _normalize_point((x2, y2), w, h)

    return p1_norm, p2_norm
