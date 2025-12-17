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
    # Giảm kích thước ảnh nếu cạnh dài nhất > 1600px để tăng tốc độ xử lý
    return clip_long_edge(bgr, max_edge)


def step2_rectify(bgr):
    """
    Step 2: Deskew - Perspective transform để straighten biển số
    Mục đích: Làm thẳng biển số bị nghiêng/xoay để OCR chính xác hơn
    """
    h, w = bgr.shape[:2]

    # Chuyển sang ảnh xám để xử lý edge detection dễ hơn
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    # Bilateral filter: Làm mịn ảnh nhưng giữ lại các cạnh quan trọng (edge-preserving smoothing)
    # d=5: Đường kính lọc, sigmaColor=60: Lọc theo màu sắc, sigmaSpace=60: Lọc theo không gian
    blur = cv2.bilateralFilter(gray, d=5, sigmaColor=60, sigmaSpace=60)

    # Canny edge detection: Xác định biên/cạnh của các đối tượng trong ảnh
    # 80, 160: Ngưỡng thấp và cao để phát hiện cạnh yếu và mạnh
    # L2gradient=True: Sử dụng L2 norm để tính gradient chính xác hơn
    edges = cv2.Canny(blur, 80, 160, L2gradient=True)

    # Morphology Close: Đóng các khoảng trống nhỏ trong biên để tạo contour liền mạch
    # Kernel 5x5 giúp kết nối các đường biên gần nhau thành 1 khối
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((5,5), np.uint8), iterations=1)

    # Find contours: Tìm các đường viền (biên ngoài) của các vùng có edge
    # RETR_EXTERNAL: Chỉ lấy contour ngoài cùng, bỏ qua các contour lồng nhau
    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Tìm contour tốt nhất (có khả năng cao là biển số)
    best, best_score = None, -1.0
    for c in cnts:
        # Tính diện tích contour
        area = cv2.contourArea(c)

        # Bỏ qua contour quá nhỏ (< 1% diện tích ảnh) - có thể là nhiễu
        if area < 0.01*w*h:
            continue

        # Tính chu vi contour
        peri = cv2.arcLength(c, True)

        # Approximate contour thành đa giác đơn giản hơn (giảm số điểm)
        # 0.02*peri: Độ chính xác approximation (2% chu vi)
        approx = cv2.approxPolyDP(c, 0.02*peri, True)

        # Kiểm tra contour có 4 góc (hình chữ nhật/hình bình hành) và lồi (convex)
        if len(approx) == 4 and cv2.isContourConvex(approx):
            # Chuyển 4 điểm góc thành mảng float32
            pts = approx.reshape(4,2).astype(np.float32)

            # Sắp xếp 4 góc theo thứ tự: top-left, top-right, bottom-right, bottom-left
            rect = order_pts(pts)
            (tl, tr, br, bl) = rect

            # Tính chiều rộng biển số (trung bình 2 cạnh ngang)
            widthA = np.linalg.norm(br - bl)  # Cạnh dưới
            widthB = np.linalg.norm(tr - tl)  # Cạnh trên

            # Tính chiều cao biển số (trung bình 2 cạnh dọc)
            heightA = np.linalg.norm(tr - br)  # Cạnh phải
            heightB = np.linalg.norm(tl - bl)  # Cạnh trái

            W = max(widthA, widthB)
            H = max(heightA, heightB)
            if H < 1 or W < 1:
                continue

            # Tính aspect ratio (tỉ lệ rộng/cao)
            ar = W / H

            # Tính điểm: Biển số VN có aspect ratio 1.2-6.0 (biển 1 dòng ~3.5, biển 2 dòng ~2.0)
            # Ưu tiên contour có aspect ratio phù hợp và diện tích lớn
            score = area * (1.0 if 1.2 <= ar <= 6.0 else 0.5)
            if score > best_score:
                best, best_score = rect, score

    # Nếu không tìm thấy contour phù hợp, trả về ảnh gốc (không deskew)
    if best is None:
        return bgr

    # Tính lại kích thước thực tế của biển số từ 4 góc tốt nhất
    widthA = np.linalg.norm(best[2] - best[3])  # Bottom
    widthB = np.linalg.norm(best[1] - best[0])  # Top
    heightA = np.linalg.norm(best[1] - best[2])  # Right
    heightB = np.linalg.norm(best[0] - best[3])  # Left
    W = int(max(widthA, widthB))
    H = int(max(heightA, heightB))

    # Chuẩn hóa kích thước output: chiều cao cố định 160px, chiều rộng tối thiểu 320px
    target_h = 160
    target_w = int(max(target_h * (W / max(H,1)), 320))

    # Định nghĩa 4 góc đích (hình chữ nhật chuẩn)
    dst = np.array([[0,0],[target_w-1,0],[target_w-1,target_h-1],[0,target_h-1]], dtype="float32")

    # Tính ma trận perspective transform từ 4 góc nguồn sang 4 góc đích
    M = cv2.getPerspectiveTransform(best, dst)

    # Áp dụng perspective transform: Chuyển biển số nghiêng thành biển số thẳng
    # INTER_CUBIC: Interpolation chất lượng cao để giữ chi tiết ký tự
    return cv2.warpPerspective(bgr, M, (target_w, target_h), flags=cv2.INTER_CUBIC)


def step3_gray_clahe(bgr_rect):
    """
    Step 3: Convert to Gray + CLAHE
    Mục đích: Tăng độ tương phản để ký tự nổi bật hơn
    """
    # Chuyển sang ảnh xám (grayscale) để giảm chiều dữ liệu và tăng tốc xử lý
    gray = cv2.cvtColor(bgr_rect, cv2.COLOR_BGR2GRAY)

    # CLAHE (Contrast Limited Adaptive Histogram Equalization):
    # Tăng độ tương phản cục bộ (adaptive) để cải thiện độ rõ nét
    # clipLimit=3.0: Giới hạn tăng contrast để tránh nhiễu (noise amplification)
    # tileGridSize=(8,8): Chia ảnh thành lưới 8x8 để xử lý từng vùng riêng biệt
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    gray_eq = clahe.apply(gray)

    return gray, gray_eq


def step4_denoise_and_sharpen(gray_eq, bilateral_d=5, sigmaC=60, sigmaS=60, unsharp_amount=0.8, unsharp_radius=1.2):
    """
    Step 4: Bilateral filter (denoise) + Unsharp masking (sharpen)
    Mục đích: Loại bỏ nhiễu nhưng giữ cạnh sắc nét, sau đó làm nét ký tự
    """
    # Bilateral filter: Làm mịn nhiễu nhưng GIỮ LẠI các cạnh của ký tự (edge-preserving)
    # d=5: Đường kính lọc
    # sigmaColor=60: Lọc các pixel có màu sắc tương tự nhau
    # sigmaSpace=60: Lọc các pixel gần nhau trong không gian
    gray_dn = cv2.bilateralFilter(gray_eq, d=bilateral_d, sigmaColor=sigmaC, sigmaSpace=sigmaS)

    # Gaussian blur: Tạo phiên bản mờ để sử dụng cho unsharp masking
    # unsharp_radius=1.2: Độ mờ (càng lớn càng mờ)
    blur = cv2.GaussianBlur(gray_dn, (0,0), unsharp_radius)

    # Unsharp masking: Làm nét ảnh bằng cách tăng cường sự khác biệt giữa ảnh gốc và ảnh mờ
    # Công thức: sharp = (1 + amount) × original - amount × blur
    # unsharp_amount=0.8: Mức độ làm nét (càng cao càng sắc nét nhưng dễ nhiễu)
    gray_refined = cv2.addWeighted(gray_dn, 1+unsharp_amount, blur, -unsharp_amount, 0)

    # Clip giá trị pixel về [0, 255] để tránh overflow/underflow
    return gray_dn, np.clip(gray_refined, 0, 255).astype(np.uint8)


# TODO: Tiền xử lý ảnh biển số
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
