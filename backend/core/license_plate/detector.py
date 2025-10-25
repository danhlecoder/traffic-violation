"""
License Plate Text Recognition using YOLO Character Detection
Pipeline: Rectify → CLAHE → Denoise → Sharpen → YOLO → Sort → Merge
"""

import os
import statistics
import numpy as np
import cv2
from typing import Optional, List, Tuple

from ...utils.logger import app_logger as logger
from ...config.config import settings

# Lazy loading YOLO model
_lp_model = None
_lp_model_path = None

# Ký tự hợp lệ cho biển số Việt Nam
ALLOWED_CHARS = [
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'K', 'L', 'M',
    'N', 'P', 'S', 'T', 'U', 'V', 'X', 'Y', 'Z'
]

def load_license_plate_model(model_path: str = None):
    """
    Load YOLO License Plate model (lazy loading)

    Args:
        model_path: Path to YOLO model file (.pt), nếu None sẽ đọc từ config
    """
    global _lp_model, _lp_model_path

    if _lp_model is not None and model_path == _lp_model_path:
        return _lp_model

    try:
        from ultralytics import YOLO

        # Đọc từ config nếu không truyền model_path
        if model_path is None:
            model_path = settings.LP_MODEL_PATH

        if not os.path.exists(model_path):
            logger.error(f"License plate model không tồn tại: {model_path}")
            return None

        logger.info(f"Loading license plate model: {model_path}")
        _lp_model = YOLO(model_path)
        _lp_model_path = model_path
        logger.info("✓ License plate model loaded")

        return _lp_model

    except Exception as e:
        logger.error(f"Lỗi load license plate model: {e}")
        return None


def order_points(pts: np.ndarray) -> np.ndarray:
    """Sắp xếp 4 điểm: TL, TR, BR, BL"""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def clip_long_edge(bgr: np.ndarray, max_len: int = 1600) -> np.ndarray:
    """Step 1: Resize ảnh nếu cạnh dài quá max_len"""
    h, w = bgr.shape[:2]
    s = min(1.0, max_len / max(h, w))
    if s < 1.0:
        return cv2.resize(bgr, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return bgr


def rectify_plate(bgr: np.ndarray) -> np.ndarray:
    """Step 2: Rectify - Perspective transform để chỉnh góc nghiêng"""
    h, w = bgr.shape[:2]
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.bilateralFilter(gray, d=5, sigmaColor=60, sigmaSpace=60)
    edges = cv2.Canny(blur, 80, 160, L2gradient=True)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=1)
    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best, best_score = None, -1.0
    for c in cnts:
        area = cv2.contourArea(c)
        if area < 0.01 * w * h:
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4 and cv2.isContourConvex(approx):
            pts = approx.reshape(4, 2).astype(np.float32)
            rect = order_points(pts)
            (tl, tr, br, bl) = rect
            widthA = np.linalg.norm(br - bl)
            widthB = np.linalg.norm(tr - tl)
            heightA = np.linalg.norm(tr - br)
            heightB = np.linalg.norm(tl - bl)
            W = max(widthA, widthB)
            H = max(heightA, heightB)
            if H < 1 or W < 1:
                continue
            ar = W / H
            score = area * (1.0 if 1.2 <= ar <= 6.0 else 0.5)
            if score > best_score:
                best, best_score = rect, score

    if best is None:
        return bgr

    widthA = np.linalg.norm(best[2] - best[3])
    widthB = np.linalg.norm(best[1] - best[0])
    heightA = np.linalg.norm(best[1] - best[2])
    heightB = np.linalg.norm(best[0] - best[3])
    W = int(max(widthA, widthB))
    H = int(max(heightA, heightB))
    target_h = 160
    target_w = int(max(target_h * (W / max(H, 1)), 320))
    dst = np.array([[0, 0], [target_w - 1, 0], [target_w - 1, target_h - 1], [0, target_h - 1]], dtype="float32")
    M = cv2.getPerspectiveTransform(best, dst)
    return cv2.warpPerspective(bgr, M, (target_w, target_h), flags=cv2.INTER_CUBIC)


def gray_clahe(bgr_rect: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Step 3: CLAHE - Contrast enhancement"""
    gray = cv2.cvtColor(bgr_rect, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray_eq = clahe.apply(gray)
    return gray, gray_eq


def denoise_and_sharpen(gray_eq: np.ndarray, bilateral_d: int = 5, sigmaC: int = 60,
                        sigmaS: int = 60, unsharp_amount: float = 0.8,
                        unsharp_radius: float = 1.2) -> Tuple[np.ndarray, np.ndarray]:
    """Step 4: Denoise + Sharpening"""
    gray_dn = cv2.bilateralFilter(gray_eq, d=bilateral_d, sigmaColor=sigmaC, sigmaSpace=sigmaS)
    blur = cv2.GaussianBlur(gray_dn, (0, 0), unsharp_radius)
    gray_refined = cv2.addWeighted(gray_dn, 1 + unsharp_amount, blur, -unsharp_amount, 0)
    return gray_dn, np.clip(gray_refined, 0, 255).astype(np.uint8)


def preprocess_for_ocr(bgr: np.ndarray, max_edge: int = 1600) -> Tuple[np.ndarray, dict]:
    """
    Pipeline: Resize → Rectify → CLAHE → Denoise → Sharpen
    Returns: (yolo_input_BGR, debug_dict)
    """
    try:
        # Step 1: Resize
        bgr_rsz = clip_long_edge(bgr, max_len=max_edge)
        
        # Step 2: Rectify
        bgr_rect = rectify_plate(bgr_rsz)
        
        # Step 3: CLAHE
        gray, gray_eq = gray_clahe(bgr_rect)
        
        # Step 4: Denoise + Sharpen
        gray_dn, gray_refined = denoise_and_sharpen(gray_eq)
        
        # Convert về BGR cho YOLO
        yolo_input = cv2.cvtColor(gray_refined, cv2.COLOR_GRAY2BGR)
        
        debug = {"bgr_rect": bgr_rect, "gray": gray, "gray_eq": gray_eq, "gray_refined": gray_refined}
        return yolo_input, debug
    except Exception as e:
        logger.error(f"Lỗi preprocess: {e}")
        return bgr, {}


def sort_boxes_two_rows(boxes_xyxy: List[List[float]]) -> List[List[int]]:
    """
    Sắp xếp boxes thành 2 hàng (biển số Việt Nam 2 dòng)

    Args:
        boxes_xyxy: List of [x1, y1, x2, y2]

    Returns:
        List of rows, mỗi row là list các indices đã sắp xếp từ trái sang phải
    """
    if not boxes_xyxy:
        return []

    # Tính center và height
    centers = [((x1 + x2) / 2.0, (y1 + y2) / 2.0) for (x1, y1, x2, y2) in boxes_xyxy]
    heights = [(y2 - y1) for (_, y1, _, y2) in boxes_xyxy]

    med_h = statistics.median(heights) if heights else 20.0
    row_thresh = 0.6 * med_h

    # Sắp xếp theo y
    order = sorted(range(len(centers)), key=lambda i: centers[i][1])

    # Nhóm thành các hàng
    rows = []
    cur = [order[0]] if order else []

    for i in order[1:]:
        if abs(centers[i][1] - centers[cur[-1]][1]) <= row_thresh:
            cur.append(i)
        else:
            rows.append(cur)
            cur = [i]

    if cur:
        rows.append(cur)

    # Sắp xếp rows theo y trung bình
    rows.sort(key=lambda idxs: statistics.mean([centers[k][1] for k in idxs]))

    # Sắp xếp trong mỗi row theo x
    return [sorted(idxs, key=lambda k: centers[k][0]) for idxs in rows]


def recognize_plate_text(plate_img: np.ndarray, conf_threshold: float = None) -> Optional[str]:
    """
    Nhận dạng text biển số bằng YOLO character detection

    Args:
        plate_img: Ảnh biển số đã crop (BGR)
        conf_threshold: Confidence threshold, nếu None sẽ đọc từ config

    Returns:
        Chuỗi biển số (format: "XX-XXXXX" hoặc "XXABXXXXX") hoặc None nếu lỗi
    """
    try:
        # Load model
        model = load_license_plate_model()
        if model is None:
            logger.warning("License plate model chưa load, bỏ qua OCR")
            return None

        # Đọc config
        if conf_threshold is None:
            conf_threshold = settings.LP_CONF_THRESHOLD
        iou_threshold = settings.LP_IOU_THRESHOLD

        # Preprocess
        yolo_img, debug = preprocess_for_ocr(plate_img)

        # Lấy class names từ model
        names = model.names
        if isinstance(names, dict):
            idx_to_name = {int(k): v for k, v in names.items()}
        else:
            idx_to_name = {i: n for i, n in enumerate(names)}

        # Tìm các class indices hợp lệ
        allowed_idx = [i for i, n in idx_to_name.items() if n in ALLOWED_CHARS]

        # Detect characters
        results = model.predict(
            source=yolo_img,
            conf=conf_threshold,
            iou=iou_threshold,
            classes=allowed_idx,
            verbose=False
        )

        if not results or len(results) == 0:
            logger.debug("YOLO OCR không detect được ký tự")
            return None

        res = results[0]

        # Extract boxes và labels
        boxes, labels = [], []
        if res.boxes is not None and len(res.boxes) > 0:
            xyxy = res.boxes.xyxy.cpu().numpy()
            cls = res.boxes.cls.cpu().numpy().astype(int)

            for (x1, y1, x2, y2), c in zip(xyxy, cls):
                name = idx_to_name.get(int(c), None)
                if name in ALLOWED_CHARS:
                    boxes.append([float(x1), float(y1), float(x2), float(y2)])
                    labels.append(name)

        if not boxes:
            logger.debug("Không có ký tự hợp lệ sau khi filter")
            return None

        # Sắp xếp thành 2 hàng
        rows = sort_boxes_two_rows(boxes)
        row_texts = ["".join([labels[k] for k in row]) for row in rows]

        # Ghép thành chuỗi biển số
        plate_text = "-".join(row_texts) if row_texts else ""

        if plate_text:
            logger.info(f"✓ OCR thành công: {plate_text}")
        else:
            logger.debug("OCR không ghép được text")

        return plate_text if plate_text else None

    except Exception as e:
        logger.error(f"Lỗi OCR biển số: {e}")
        return None
