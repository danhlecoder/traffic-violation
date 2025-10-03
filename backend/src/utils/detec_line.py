import math
from typing import Optional, Tuple

import cv2
import numpy as np


def _normalize_point(pt: Tuple[float, float], width: int, height: int) -> Tuple[float, float]:
    x, y = pt
    if width <= 0 or height <= 0:
        return 0.0, 0.0
    return float(np.clip(x / float(width), 0.0, 1.0)), float(np.clip(y / float(height), 0.0, 1.0))


def _extend_line_to_frame(x1: float, y1: float, x2: float, y2: float, w: int, h: int) -> Tuple[float, float, float, float]:
    """Kéo dài đoạn thẳng tới biên ảnh theo logic trong notebook."""
    dx, dy = x2 - x1, y2 - y1
    if abs(dx) >= abs(dy):
        denom = dx if dx != 0 else 1e-6
        yL = y1 + dy * (0 - x1) / denom
        yR = y1 + dy * ((w - 1) - x1) / denom
        p1 = (0.0, float(np.clip(yL, 0, h - 1)))
        p2 = (float(w - 1), float(np.clip(yR, 0, h - 1)))
    else:
        denom = dy if dy != 0 else 1e-6
        xT = x1 + dx * (0 - y1) / denom
        xB = x1 + dx * ((h - 1) - y1) / denom
        p1 = (float(np.clip(xT, 0, w - 1)), 0.0)
        p2 = (float(np.clip(xB, 0, w - 1)), float(h - 1))
    return p1[0], p1[1], p2[0], p2[1]


def center_crop_to_16_9(frame_bgr: np.ndarray) -> np.ndarray:
    """Cắt giữa ảnh về đúng tỉ lệ 16:9 mà không làm méo (giữ nguyên scale)."""
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
        # Quá rộng: cắt bớt chiều ngang
        new_w = int(round(h * target))
        x0 = max(0, (w - new_w) // 2)
        x1 = min(w, x0 + new_w)
        return frame_bgr[:, x0:x1]
    else:
        # Quá cao: cắt bớt chiều dọc
        new_h = int(round(w / target))
        y0 = max(0, (h - new_h) // 2)
        y1 = min(h, y0 + new_h)
        return frame_bgr[y0:y1, :]


def detect_stop_line_points(frame_bgr: np.ndarray) -> Optional[Tuple[Tuple[float, float], Tuple[float, float]]]:
    """
    Phát hiện vạch dừng theo từng bước:
    1) Grayscale
    2) Gaussian blur nhẹ
    3) Canny edge
    4) HoughLinesP
    5) Lọc đường gần ngang, gần tâm theo trục x và gần đáy ảnh
    6) Kéo dài đoạn thẳng tới biên ảnh và trả về 2 điểm (pixel)
    """
    if frame_bgr is None or frame_bgr.size == 0:
        return None

    img_h, img_w = frame_bgr.shape[:2]

    # 1) Grayscale
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    # 2) Gaussian blur nhẹ (kernel lẻ 3x3)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    # 3) Canny (50, 50) như notebook
    edges = cv2.Canny(blur, 50, 50)

    # Giới hạn ROI: đáy khung và gần trung tâm ngang để giảm nhiễu 2 bên
    roi_mask = np.zeros_like(edges, dtype=np.uint8)
    y0 = int(img_h * 0.6)
    x_left = int(img_w * 0.15)
    x_right = int(img_w * 0.85)
    roi_mask[y0:img_h, x_left:x_right] = 255
    edges = cv2.bitwise_and(edges, roi_mask)

    # Kết nối vạch đứt bằng morphology đóng theo phương ngang
    k_w = max(9, int(img_w * 0.04))
    if k_w % 2 == 0:
        k_w += 1
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k_w, 1))
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=1)

    # 4) HoughLinesP (tham số theo tỉ lệ kích thước để ổn định giữa các nguồn)
    min_len = max(60, int(img_w * 0.25))
    max_gap = max(10, int(img_w * 0.02))
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=100,
        minLineLength=min_len,
        maxLineGap=max_gap,
    )
    if lines is None or len(lines) == 0:
        return None

    # 5) Lọc: gần ngang (góc < 10°), gần tâm theo x, và gần đáy (y > 60% h)
    # Gom các đoạn thẳng ứng viên rồi fit tuyến tính có trọng số (độ dài)
    best_line = None
    best_y = -1.0
    xs: list[float] = []
    ys: list[float] = []
    ws: list[float] = []
    for line in lines:
        x1, y1, x2, y2 = [float(v) for v in line[0]]
        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)
        if length < min_len * 0.5:
            continue
        angle = abs(math.degrees(math.atan2(dy, dx)))
        if angle >= 10.0:
            continue
        avg_y = (y1 + y2) / 2.0
        avg_x = (x1 + x2) / 2.0
        if abs(avg_x - (img_w / 2.0)) < (img_w * 0.35) and avg_y > (img_h * 0.6):
            # Lưu lại tuyến tính tốt nhất để fallback
            if avg_y > best_y:
                best_y = avg_y
                best_line = (x1, y1, x2, y2)
            # Thu thập điểm cho hồi quy
            xs += [x1, x2]
            ys += [y1, y2]
            ws += [length, length]

    if len(xs) >= 2:
        try:
            coeffs = np.polyfit(np.asarray(xs), np.asarray(ys), 1, w=np.asarray(ws))
            a, b = float(coeffs[0]), float(coeffs[1])  # y = a*x + b
            y_left = a * 0.0 + b
            y_right = a * (img_w - 1.0) + b
            p1 = (0.0, float(np.clip(y_left, 0, img_h - 1)))
            p2 = (float(img_w - 1), float(np.clip(y_right, 0, img_h - 1)))
            return p1, p2
        except Exception:
            pass

    # Fallback: dùng đoạn thẳng tốt nhất và kéo dài ra biên
    if best_line is None:
        return None
    ex1, ey1, ex2, ey2 = _extend_line_to_frame(*best_line, img_w, img_h)
    return (ex1, ey1), (ex2, ey2)


def detect_stop_line_normalized(frame_bgr: np.ndarray) -> Optional[Tuple[Tuple[float, float], Tuple[float, float]]]:
    """Trả về 2 điểm đã chuẩn hóa (0..1) nếu phát hiện được vạch dừng."""
    result = detect_stop_line_points(frame_bgr)
    if result is None:
        return None
    (x1, y1), (x2, y2) = result
    h, w = frame_bgr.shape[:2]
    p1n = _normalize_point((x1, y1), w, h)
    p2n = _normalize_point((x2, y2), w, h)
    return p1n, p2n


