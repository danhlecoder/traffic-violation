"""
Enhanced Preprocessing cho License Plate OCR
Deskew + CLAHE + Denoise + Sharpen - CHÍNH XÁC THEO CODE MẪU
"""

import statistics
import numpy as np
import cv2


def clip_long_edge(bgr, max_len=1600):
    """Resize ảnh nếu cạnh dài nhất > max_len"""
    h, w = bgr.shape[:2]
    s = min(1.0, max_len / max(h, w))
    return cv2.resize(bgr, (int(w*s), int(h*s)), interpolation=cv2.INTER_AREA) if s < 1.0 else bgr


def order_pts(pts):
    """Sắp xếp 4 điểm theo thứ tự: TL, TR, BR, BL"""
    rect = np.zeros((4,2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


# ======================= TIỀN XỬ LÝ TỪNG BƯỚC =======================
def step1_resize(bgr, max_edge=1600):
    """Step 1: Resize ảnh nếu quá lớn"""
    return clip_long_edge(bgr, max_edge)


def step2_rectify(bgr):
    """Step 2: Deskew - Perspective transform để straighten biển số"""
    h, w = bgr.shape[:2]
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.bilateralFilter(gray, d=5, sigmaColor=60, sigmaSpace=60)
    edges = cv2.Canny(blur, 80, 160, L2gradient=True)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((5,5), np.uint8), iterations=1)
    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    best, best_score = None, -1.0
    for c in cnts:
        area = cv2.contourArea(c)
        if area < 0.01*w*h:
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02*peri, True)
        if len(approx) == 4 and cv2.isContourConvex(approx):
            pts = approx.reshape(4,2).astype(np.float32)
            rect = order_pts(pts)
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
    target_w = int(max(target_h * (W / max(H,1)), 320))
    dst = np.array([[0,0],[target_w-1,0],[target_w-1,target_h-1],[0,target_h-1]], dtype="float32")
    M = cv2.getPerspectiveTransform(best, dst)
    return cv2.warpPerspective(bgr, M, (target_w, target_h), flags=cv2.INTER_CUBIC)


def step3_gray_clahe(bgr_rect):
    """Step 3: Convert to Gray + CLAHE"""
    gray = cv2.cvtColor(bgr_rect, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    gray_eq = clahe.apply(gray)
    return gray, gray_eq


def step4_denoise_and_sharpen(gray_eq, bilateral_d=5, sigmaC=60, sigmaS=60, unsharp_amount=0.8, unsharp_radius=1.2):
    """Step 4: Bilateral filter (denoise) + Unsharp masking (sharpen)"""
    gray_dn = cv2.bilateralFilter(gray_eq, d=bilateral_d, sigmaColor=sigmaC, sigmaSpace=sigmaS)
    blur = cv2.GaussianBlur(gray_dn, (0,0), unsharp_radius)
    gray_refined = cv2.addWeighted(gray_dn, 1+unsharp_amount, blur, -unsharp_amount, 0)
    return gray_dn, np.clip(gray_refined, 0, 255).astype(np.uint8)


def preprocess_enhanced(bgr, max_edge=1600):
    """
    Full preprocessing pipeline - CHÍNH XÁC THEO CODE MẪU
    
    Returns:
        yolo_input: BGR image ready for YOLO
        debug: Dict với các bước trung gian
    """
    try:
        bgr_rsz = step1_resize(bgr, max_edge=max_edge)
        bgr_rect = step2_rectify(bgr_rsz)
        gray, gray_eq = step3_gray_clahe(bgr_rect)
        gray_dn, gray_refined = step4_denoise_and_sharpen(gray_eq)
        yolo_input = cv2.cvtColor(gray_refined, cv2.COLOR_GRAY2BGR)
        debug = {"bgr_rect": bgr_rect, "gray": gray, "gray_eq": gray_eq, "gray_refined": gray_refined}
        return yolo_input, debug
    except Exception:
        # Fallback: return ảnh gốc nếu preprocessing fail
        return bgr, {}


def sort_boxes_two_rows(boxes_xyxy):
    """
    Sắp xếp boxes theo 2 hàng (biển số 2 dòng)
    CHÍNH XÁC THEO CODE MẪU
    """
    if not boxes_xyxy:
        return []
    
    centers = [((x1+x2)/2.0, (y1+y2)/2.0) for (x1,y1,x2,y2) in boxes_xyxy]
    heights = [(y2-y1) for (_,y1,_,y2) in boxes_xyxy]
    med_h = statistics.median(heights) if heights else 20.0
    row_thresh = 0.6 * med_h
    
    order = sorted(range(len(centers)), key=lambda i: centers[i][1])
    rows, cur = [], [order[0]] if order else []
    
    for i in order[1:]:
        if abs(centers[i][1] - centers[cur[-1]][1]) <= row_thresh:
            cur.append(i)
        else:
            rows.append(cur)
            cur = [i]
    if cur:
        rows.append(cur)
    
    rows.sort(key=lambda idxs: statistics.mean([centers[k][1] for k in idxs]))
    return [sorted(idxs, key=lambda k: centers[k][0]) for idxs in rows]
