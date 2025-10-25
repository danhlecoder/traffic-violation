"""
Computer Vision Service - Stop Line Detection

Logic:
1. LUÔN thử HoughLinesP (Canny edge detection) để phát hiện đường ngang
2. Nếu thành công → trả về stopline phát hiện được
3. Nếu thất bại → fallback về line mặc định tại 2/3 chiều cao ảnh
"""

import math
from typing import Optional, Tuple, List
import cv2
import numpy as np

from ...config.config import settings
from ...utils.logger import app_logger as logger
from ...utils.image import normalize_point, extend_line_to_frame


Point = Tuple[float, float]
Segment = Tuple[Point, Point]


def detect_stop_line_points(frame_bgr: np.ndarray) -> Optional[Segment]:
    """
    Phát hiện vạch dừng sử dụng Canny + HoughLinesP
    
    Args:
        frame_bgr: Frame ảnh BGR
    
    Returns:
        Tuple 2 điểm (x1,y1), (x2,y2) đã kéo dài tới biên, hoặc None
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
        ex1, ey1, ex2, ey2 = extend_line_to_frame(*best_line, img_w, img_h)
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

    p1_norm = normalize_point((x1, y1), w, h)
    p2_norm = normalize_point((x2, y2), w, h)

    return p1_norm, p2_norm


def _create_default_stopline() -> Segment:
    """
    Tạo line ngang mặc định ở vị trí 2/3 chiều cao ảnh

    Returns:
        Tuple 2 điểm chuẩn hóa tại y = 2/3
    """
    y_position = 2.0 / 3.0
    logger.info(f"📏 Tạo stopline mặc định ở y={y_position:.3f} (2/3 chiều cao)")
    return (0.0, y_position), (1.0, y_position)


def calculate_lineB_from_stopline(
    stopline_result: Tuple[Tuple[float, float], Tuple[float, float]],
    image_height: int,
    offset_px: int = 64
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """
    Tính toán lineB từ stopLine bằng cách offset lên trên offset_px pixels

    Args:
        stopline_result: Tuple 2 điểm của stopLine đã normalize ((x1,y1), (x2,y2))
        image_height: Chiều cao ảnh gốc (px)
        offset_px: Khoảng cách offset (px), mặc định 64px

    Returns:
        Tuple 2 điểm của lineB đã normalize
    """
    (x1, y1), (x2, y2) = stopline_result

    # Chuyển y về pixel
    y1_px = y1 * image_height
    y2_px = y2 * image_height

    # Offset lên trên
    y1_new_px = y1_px - offset_px
    y2_new_px = y2_px - offset_px

    # Normalize lại
    y1_new = y1_new_px / image_height
    y2_new = y2_new_px / image_height

    # Clamp trong [0, 1]
    y1_new = max(0.0, min(1.0, y1_new))
    y2_new = max(0.0, min(1.0, y2_new))

    return (x1, y1_new), (x2, y2_new)


def calculate_roi_from_lineB(
    lineB_result: Tuple[Tuple[float, float], Tuple[float, float]]
) -> List[Tuple[float, float]]:
    """
    Tạo ROI tự động từ lineB
    ROI là hình thang với:
    - Cạnh trên: CHÍNH XÁC lineB (giữ nguyên 2 điểm, có thể xiên)
    - Cạnh dưới: đáy stream (y=1)

    Args:
        lineB_result: Tuple 2 điểm của lineB đã normalize ((x1,y1), (x2,y2))

    Returns:
        List 4 điểm tạo thành ROI [top-left, top-right, bottom-right, bottom-left]
    """
    (x1, y1), (x2, y2) = lineB_result

    # ROI từ lineB xuống đáy stream
    # Cạnh trên = lineB (GIỮ NGUYÊN 2 điểm, có thể xiên!)
    roi_points = [
        (x1, y1),          # Top-left: điểm trái của lineB
        (x2, y2),          # Top-right: điểm phải của lineB  
        (1.0, 1.0),        # Bottom-right: góc phải đáy
        (0.0, 1.0),        # Bottom-left: góc trái đáy
    ]

    return roi_points


def detect_stop_line_with_fallback(frame_bgr: np.ndarray) -> Optional[Segment]:
    """
    Phát hiện vạch dừng với fallback:
    
    1. LUÔN thử HoughLinesP (Canny edge detection) trước
    2. Nếu THÀNH CÔNG → trả về kết quả
    3. Nếu THẤT BẠI → fallback về line mặc định 2/3 chiều cao

    Args:
        frame_bgr: Frame ảnh BGR (thường là frame đầu tiên)

    Returns:
        Tuple 2 điểm chuẩn hóa [0..1]
    """
    if frame_bgr is None or frame_bgr.size == 0:
        logger.warning("Frame rỗng, sử dụng default line")
        return _create_default_stopline()

    try:
        # Bước 1: LUÔN thử HoughLinesP trước
        logger.info("🔍 Thử phát hiện stopline bằng HoughLinesP (Canny + edge detection)...")
        result = detect_stop_line_normalized(frame_bgr)
        
        if result is not None:
            logger.info("✓ Detect stopline thành công bằng HoughLinesP")
            return result
        else:
            # Bước 2: Fallback về mặc định 2/3
            logger.warning("⚠️ HoughLinesP không tìm thấy đường ngang → Fallback về mặc định 2/3")
            return _create_default_stopline()

    except Exception as e:
        logger.error(f"Lỗi trong detect_stop_line_with_fallback: {e}")
        return _create_default_stopline()
