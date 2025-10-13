"""
Các hàm tiện ích phát hiện vạch dừng (stop line) từ ảnh BGR.
Mục tiêu refactor:
- Làm rõ quy trình xử lý, loại bỏ magic-number rải rác.
- Gắn comment/giải thích bằng tiếng Việt để dễ bảo trì.
- Giữ nguyên API công khai đang được nơi khác dùng:
  - center_crop_to_16_9(frame_bgr) -> np.ndarray
  - detect_stop_line_normalized(frame_bgr) -> Optional[((x,y),(x,y))] (tọa độ chuẩn hóa 0..1)
"""
import math
from typing import Optional, Tuple
import cv2
import numpy as np
# Kiểu dữ liệu tiện dụng
Point = Tuple[float, float]
Segment = Tuple[Point, Point]
# Các hằng số tham số hóa thuật toán (dễ chỉnh/tinh).
# Canny
CANNY_LOW = 50
CANNY_HIGH = 50
# HoughLinesP
HOUGH_RHO = 1
HOUGH_THETA = np.pi / 180
HOUGH_THRESHOLD = 100
MIN_LINE_LEN_FACTOR = 0.25  # theo tỉ lệ bề ngang ảnh
MAX_GAP_FACTOR = 0.02       # theo tỉ lệ bề ngang ảnh
MIN_LINE_LEN_MIN_PX = 60
MAX_GAP_MIN_PX = 10
# Tiêu chí lọc đoạn thẳng thành vạch dừng
ANGLE_MAX_DEG = 10.0        # gần ngang
CENTER_BIAS_RATIO = 0.35    # gần tâm theo trục x
BOTTOM_MIN_Y_RATIO = 0.60   # ưu tiên nửa dưới ảnh
def _normalize_point(pt: Point, width: int, height: int) -> Point:
    """Chuẩn hóa tọa độ pixel về khoảng [0..1] theo (x/width, y/height)."""
    x, y = pt
    if width <= 0 or height <= 0:
        return 0.0, 0.0
def _extend_line_to_frame(x1: float, y1: float, x2: float, y2: float, w: int, h: int) -> Tuple[float, float, float, float]:
    """
    Kéo dài đoạn thẳng (x1,y1)-(x2,y2) tới biên ảnh (0..w-1, 0..h-1).
    - Nếu phương ngang trội (|dx|>=|dy|): lấy giao điểm với hai biên trái/phải.
    - Nếu phương dọc trội: lấy giao điểm với hai biên trên/dưới.
    Trả về 4 giá trị (ex1, ey1, ex2, ey2) nằm trong khung hình.
    """
    dx, dy = x2 - x1, y2 - y1
    if abs(dx) >= abs(dy):
        denom = dx if dx != 0 else 1e-6
def center_crop_to_16_9(frame_bgr: np.ndarray) -> np.ndarray:
    """
    Cắt giữa khung hình về đúng tỉ lệ 16:9 (không kéo giãn)
    - Nếu ảnh đã đúng 16:9 thì trả về nguyên vẹn.
    - Nếu quá rộng: cắt bớt chiều ngang; nếu quá cao: cắt bớt chiều dọc.
    """
    if frame_bgr is None or frame_bgr.size == 0:
        return frame_bgr
    h, w = frame_bgr.shape[:2]
    if h == 0 or w == 0:
        return frame_bgr
    target = 16.0 / 9.0
    ratio = float(w) / float(h)
    if abs(ratio - target) < 1e-3:
        return frame_bgr
    if ratio > target:
        # Ảnh quá rộng so với 16:9 -> cắt bớt bề ngang, giữ chiều cao
        new_w = int(round(h * target))
        x0 = max(0, (w - new_w) // 2)
        x1 = min(w, x0 + new_w)
        return frame_bgr[:, x0:x1]
    else:
        # Ảnh quá cao -> cắt bớt bề dọc, giữ bề ngang
        new_h = int(round(w / target))
        y0 = max(0, (h - new_h) // 2)
        y1 = min(h, y0 + new_h)
        return frame_bgr[y0:y1, :]
def detect_stop_line_points(frame_bgr: np.ndarray) -> Optional[Segment]:
    """
    Phát hiện vạch dừng và trả về 2 điểm pixel đã được kéo dài ra hai biên khung hình.
    Quy trình:
    1) Chuyển xám -> làm mịn Gaussian(3x3) -> biên Canny.
    2) HoughLinesP tìm các đoạn thẳng.
    3) Lọc các đoạn gần như nằm ngang, gần tâm theo trục X và nằm ở nửa dưới ảnh;
       chọn đoạn có tung độ trung bình (avg_y) lớn nhất => ưu tiên gần đáy.
    4) Kéo dài đoạn đã chọn ra tới biên khung hình.
    """
    if frame_bgr is None or frame_bgr.size == 0:
        return None
    img_h, img_w = frame_bgr.shape[:2]
    if img_h <= 0 or img_w <= 0:
        return None
    # 1) Tiền xử lý biên
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blur, CANNY_LOW, CANNY_HIGH)
    # 2) Tìm đoạn thẳng bằng HoughLinesP
    min_len = max(MIN_LINE_LEN_MIN_PX, int(img_w * MIN_LINE_LEN_FACTOR))
    max_gap = max(MAX_GAP_MIN_PX, int(img_w * MAX_GAP_FACTOR))
    lines = cv2.HoughLinesP(
        edges,
        rho=HOUGH_RHO,
        theta=HOUGH_THETA,
        threshold=HOUGH_THRESHOLD,
        minLineLength=min_len,
        maxLineGap=max_gap,
    )
    if lines is None or len(lines) == 0:
        return None
    # 3) Chọn đoạn "tốt nhất" theo tiêu chí đã mô tả
    best_line: Optional[Tuple[float, float, float, float]] = None
    best_avg_y = -1.0
    center_x = img_w / 2.0
    for line in lines:
        x1, y1, x2, y2 = [float(v) for v in line[0]]
        dx, dy = (x2 - x1), (y2 - y1)
        angle = abs(math.degrees(math.atan2(dy, dx)))
        if angle >= ANGLE_MAX_DEG:
            continue  # không gần ngang
        avg_y = (y1 + y2) / 2.0
        avg_x = (x1 + x2) / 2.0
        near_center = abs(avg_x - center_x) < (img_w * CENTER_BIAS_RATIO)
        near_bottom = avg_y > (img_h * BOTTOM_MIN_Y_RATIO)
        if near_center and near_bottom and avg_y > best_avg_y:
            best_avg_y = avg_y
            best_line = (x1, y1, x2, y2)
    if best_line is None:
        return None
    # 4) Kéo dài ra biên và trả về 2 điểm pixel
    ex1, ey1, ex2, ey2 = _extend_line_to_frame(*best_line, img_w, img_h)
    return (ex1, ey1), (ex2, ey2)
def detect_stop_line_normalized(frame_bgr: np.ndarray) -> Optional[Segment]:
    """
    Phát hiện vạch dừng và trả về 2 điểm đã chuẩn hóa [0..1].
    Trả về None nếu không tìm thấy.
    """
    result = detect_stop_line_points(frame_bgr)
    if result is None:
        return None
    (x1, y1), (x2, y2) = result
    h, w = frame_bgr.shape[:2]
    p1n = _normalize_point((x1, y1), w, h)
    p2n = _normalize_point((x2, y2), w, h)
    return p1n, p2n
