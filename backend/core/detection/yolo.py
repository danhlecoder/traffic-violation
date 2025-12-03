"""
YOLO Detector - Local Model Loading (5-10x faster than API)
"""

from typing import List, Dict, Any
import numpy as np
import cv2
from ...config.config import settings
from ...utils.logger import app_logger as logger


class YOLODetector:
    """YOLO Detector - Load model cục bộ (nhanh hơn 5-10x so với API)"""

    def __init__(self):
        try:
            from ultralytics import YOLO
            import torch

            # Load model từ file
            model_path = settings.YOLO_MODEL_PATH
            logger.info(f"Loading YOLO model from: {model_path}")

            self.model = YOLO(model_path)

            # Chọn device: mặc định GPU (cuda), fallback CPU nếu không có
            configured = (settings.YOLO_DEVICE or 'cuda').lower()

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
                logger.info(f"✓ YOLO running on GPU: {torch.cuda.get_device_name(0)}")
            else:
                device = 'cpu'
                self.device = device
                self.model.to('cpu')
                if configured == 'cuda':
                    logger.warning("⚠️ GPU không khả dụng, fallback sang CPU")
                else:
                    logger.info("✓ YOLO running on CPU (cấu hình thủ công)")

            # Default thresholds
            self.default_conf = settings.YOLO_CONF_DEFAULT
            self.default_iou = settings.YOLO_IOU_DEFAULT

            logger.info(f"✓ YOLO Detector initialized (LOCAL mode, device={device})")

        except Exception as e:
            logger.error(f"❌ Failed to load YOLO model: {e}")
            raise

    def detect(self, frame: np.ndarray, conf: float = None, iou: float = None) -> List[Dict[str, Any]]:
        """
        Phát hiện đối tượng bằng model local

        Args:
            frame: BGR image (numpy array)
            conf: Confidence threshold (None = dùng default từ config)
            iou: IOU threshold (None = dùng default từ config)

        Returns:
            Danh sách detections: [{"bbox": [x1,y1,x2,y2], "confidence": 0.9, "class_name": "car"}, ...]
        """
        if conf is None:
            conf = self.default_conf
        if iou is None:
            iou = self.default_iou

        try:
            # Run inference (verbose=False để giảm logs)
            results = self.model.predict(
                source=frame,
                conf=conf,
                iou=iou,
                device=self.device,
                verbose=False,
                stream=False
            )

            # Parse results
            detections = []
            if results and len(results) > 0:
                result = results[0]
                boxes = result.boxes

                if boxes is not None and len(boxes) > 0:
                    for box in boxes:
                        # Get bbox coordinates
                        xyxy = box.xyxy[0].cpu().numpy()  # [x1, y1, x2, y2]

                        # Get confidence and class
                        confidence = float(box.conf[0].cpu().numpy())
                        class_id = int(box.cls[0].cpu().numpy())
                        class_name = self.model.names[class_id]

                        detections.append({
                            "bbox": xyxy.tolist(),
                            "confidence": confidence,
                            "class_name": class_name,
                            "class_id": class_id
                        })

            return detections

        except Exception as e:
            logger.error(f"Error during detection: {e}")
            return []

    def draw_detections(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """Vẽ bounding boxes với màu sắc khác nhau cho mỗi class"""
        # Định nghĩa màu sắc cho mỗi loại phương tiện (BGR format)
        CLASS_COLORS = {
            'car': (0, 255, 0),          # Green - Xe hơi
            'motorcycle': (0, 165, 255), # Orange - Xe máy
            'truck': (255, 0, 0),        # Blue - Xe tải
            'bus': (255, 255, 0),        # Cyan - Xe bus
            'bicycle': (0, 255, 255),    # Yellow - Xe đạp
            'license_plate': (255, 0, 255),  # Magenta - Biển số
            'light_red': (0, 0, 255),    # Red - Đèn đỏ
            'light_green': (0, 255, 0),  # Green - Đèn xanh
            'light_yellow': (0, 255, 255), # Yellow - Đèn vàng
            'helmet': (255, 255, 255),   # White - Mũ bảo hiểm
            'no_helmet': (0, 0, 255),    # Red - Không mũ
        }

        for det in detections:
            bbox = det.get("bbox")
            if not bbox or len(bbox) != 4:
                continue

            x1, y1, x2, y2 = map(int, bbox)

            # Lấy thông tin class
            class_name = det.get('class_name', 'obj')
            confidence = det.get('confidence', 0)
            track_id = det.get('track_id')

            # Chọn màu theo class, mặc định xám nếu không rõ
            color = CLASS_COLORS.get(class_name, (128, 128, 128))

            # Xây dựng nhãn
            if track_id is not None:
                label = f"ID:{track_id} {class_name} {confidence:.2f}"
            else:
                label = f"{class_name} {confidence:.2f}"

            # Vẽ bbox và nhãn
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        return frame


# Singleton
_detector_instance = None

def get_yolo_detector() -> YOLODetector:
    """Lấy YOLO detector instance (API client)"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = YOLODetector()
    return _detector_instance
