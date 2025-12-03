"""
License Plate OCR - YOLO Local Model
Enhanced với preprocessing + ALLOWED_CHARS filtering - CHÍNH XÁC THEO CODE MẪU
"""

import numpy as np
from typing import Optional, List
from ...config.config import settings
from ...utils.logger import app_logger as logger

# CHỈ DÙNG CÁC KÝ TỰ NÀY - CHÍNH XÁC THEO CODE MẪU
ALLOWED_CHARS = [
    '0','1','2','3','4','5','6','7','8','9',
    'A','B','C','D','E','F','G','H','K','L','M',
    'N','P','S','T','U','V','X','Y','Z'
]


class LicensePlateOCR:
    """License Plate OCR - Local YOLO model"""

    def __init__(self):
        try:
            from ultralytics import YOLO
            import torch

            model_path = settings.LP_MODEL_PATH
            logger.info(f"Loading License Plate OCR model from: {model_path}")

            self.model = YOLO(model_path)

            # Chọn device: mặc định GPU (cuda), fallback CPU nếu không có
            configured = (settings.LP_DEVICE or 'cuda').lower()

            # Ưu tiên GPU: nếu config là cuda hoặc auto
            if configured in ('cuda', 'auto') and torch.cuda.is_available():
                device = '0'
                self.device = device
                self.model.to('cuda')
                try:
                    torch.backends.cudnn.benchmark = True
                    # Half precision để tăng tốc độ
                    self.model.model.half()  # type: ignore[attr-defined]
                except Exception:
                    pass
                logger.info("✓ License Plate OCR running on GPU")
            else:
                device = 'cpu'
                self.device = device
                self.model.to('cpu')
                if configured == 'cuda':
                    logger.warning("⚠️ GPU không khả dụng cho LP OCR, fallback sang CPU")
                else:
                    logger.info("✓ License Plate OCR running on CPU (cấu hình thủ công)")

            # Build ALLOWED_IDX từ model.names - CHÍNH XÁC THEO CODE MẪU
            names = self.model.names
            if isinstance(names, dict):
                self.idx_to_name = {int(k): v for k, v in names.items()}
            else:
                self.idx_to_name = {i: n for i, n in enumerate(names)}

            # Chỉ số lớp được phép (tìm theo tên)
            self.allowed_idx = [i for i, n in self.idx_to_name.items() if n in ALLOWED_CHARS]

            logger.info(f"✓ License Plate OCR initialized (LOCAL mode, device={device})")
            logger.info(f"✓ Allowed classes: {len(self.allowed_idx)}/{len(self.idx_to_name)} chars")

        except Exception as e:
            logger.error(f"❌ Failed to load License Plate OCR model: {e}")
            raise

    def recognize(self, plate_img: np.ndarray) -> Optional[str]:
        """
        Nhận dạng ký tự biển số - CHÍNH XÁC THEO CODE MẪU

        Args:
            plate_img: Ảnh biển số đã preprocessing (BGR)

        Returns:
            Text biển số (e.g. "30A-12345") hoặc None
        """
        try:
            # Import sort_boxes_two_rows
            from .preprocessing import sort_boxes_two_rows

            # Detect với confidence thấp hơn để tăng recall (nhận diện nhiều ký tự hơn)
            # Dùng settings.LP_CONF_THRESHOLD (default 0.25) thay vì hardcode 0.35
            from ...config.config import settings
            conf_threshold = settings.LP_CONF_THRESHOLD if hasattr(settings, 'LP_CONF_THRESHOLD') else 0.25

            results = self.model.predict(
                source=plate_img,
                conf=conf_threshold,
                iou=0.6,
                classes=self.allowed_idx,
                device=self.device,
                verbose=False
            )

            if not results or len(results) == 0:
                return None

            result = results[0]

            # Lấy nhãn & ráp chuỗi (lọc dự phòng theo ALLOWED_CHARS) - CHÍNH XÁC THEO CODE MẪU
            boxes, labels = [], []
            if result.boxes is not None and len(result.boxes) > 0:
                xyxy = result.boxes.xyxy.cpu().numpy()
                cls = result.boxes.cls.cpu().numpy().astype(int)
                for (x1,y1,x2,y2), c in zip(xyxy, cls):
                    name = self.idx_to_name.get(int(c), None)
                    if name in ALLOWED_CHARS:  # chỉ nhận ký tự cho phép
                        boxes.append([float(x1), float(y1), float(x2), float(y2)])
                        labels.append(name)

            if not boxes:
                return None

            # Sort boxes theo 2 hàng - CHÍNH XÁC THEO CODE MẪU
            rows = sort_boxes_two_rows(boxes)
            row_texts = ["".join([labels[k] for k in row]) for row in rows]
            plate_text = "-".join(row_texts) if row_texts else ""

            return plate_text if plate_text else None

        except Exception as e:
            logger.error(f"Error during plate OCR: {e}")
            return None


# Singleton
_lp_ocr_instance = None

def get_license_plate_ocr() -> LicensePlateOCR:
    """Lấy License Plate OCR instance"""
    global _lp_ocr_instance
    if _lp_ocr_instance is None:
        _lp_ocr_instance = LicensePlateOCR()
    return _lp_ocr_instance


def recognize_plate_text(plate_img: np.ndarray, conf_threshold: float = None) -> Optional[str]:
    """
    OCR biển số với enhanced preprocessing

    Quy trình:
    1. Preprocess: Deskew + CLAHE + Denoise + Sharpen
    2. Detect characters bằng YOLO OCR model (server.yaml line 27-32)
    3. Sort boxes theo 2 hàng (biển số 2 dòng)
    4. Ghép text: Hàng 1 - Hàng 2

    Args:
        plate_img: Plate crop image (BGR)
        conf_threshold: Không dùng (lấy từ settings)

    Returns:
        Plate text (e.g. "30A-12345") or None
    """
    try:
        # Import preprocessing
        from .preprocessing import preprocess_enhanced

        # 1-4) Tiền xử lý: Deskew + CLAHE + Denoise + Sharpen
        yolo_img, debug = preprocess_enhanced(plate_img, max_edge=1600)

        # 5) Detect characters bằng License Plate OCR model
        ocr = get_license_plate_ocr()
        plate_text = ocr.recognize(yolo_img)

        return plate_text

    except Exception as e:
        logger.error(f"OCR error: {e}")
        return None
