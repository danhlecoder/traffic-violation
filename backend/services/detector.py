"""
YOLO Detector - Service phát hiện đối tượng sử dụng YOLOv8

Chức năng:
- Load YOLO model (singleton pattern)
- Detect objects trên frame
- Vẽ bounding boxes với labels
"""

import os
from typing import Optional, List, Dict, Any
import numpy as np
import cv2
from pathlib import Path

from ..core.config import settings
from ..core.constants import COLORS_BY_CLASS, DEFAULT_COLOR
from ..utils.logger import app_logger as logger


class YOLODetector:
    """
    Service phát hiện đối tượng sử dụng YOLO

    Chức năng:
    - Load model YOLO một lần duy nhất (singleton)
    - Detect objects trên frame
    - Vẽ bounding boxes và labels lên frame
    """

    def __init__(self):
        self._model = None
        self._model_loaded = False
        self._model_path = settings.YOLO_MODEL_PATH
        self._confidence = settings.YOLO_CONFIDENCE
        self._iou_threshold = settings.YOLO_IOU_THRESHOLD
        self._device = settings.YOLO_DEVICE

    def _load_model(self):
        """
        Load YOLO model từ file
        Chỉ load một lần duy nhất
        """
        if self._model_loaded:
            return

        try:
            # Import ultralytics YOLO
            from ultralytics import YOLO

            # Kiểm tra file model tồn tại
            model_path = Path(self._model_path)
            if not model_path.exists():
                logger.error(f"Không tìm thấy file model YOLO tại: {self._model_path}")
                raise FileNotFoundError(f"Model file not found: {self._model_path}")

            self._model = YOLO(str(model_path))
            self._model_loaded = True

        except ImportError:
            logger.error("Không tìm thấy thư viện ultralytics. Vui lòng cài đặt: pip install ultralytics")
            raise
        except Exception as e:
            logger.error(f"Lỗi khi load YOLO model: {e}")
            raise

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Phát hiện đối tượng trên frame
        
        Args:
            frame: Frame ảnh (BGR format)
            
        Returns:
            List các detection, mỗi detection bao gồm:
            - bbox: [x1, y1, x2, y2]
            - confidence: độ tin cậy
            - class_id: ID của class
            - class_name: tên class (tiếng Anh)
        """
        if not self._model_loaded:
            self._load_model()

        if self._model is None:
            logger.warning("Model chưa được load, bỏ qua detection")
            return []

        try:
            # Chạy inference
            results = self._model(
                frame,
                conf=self._confidence,
                iou=self._iou_threshold,
                device=self._device,
                verbose=False
            )

            detections = []

            # Parse kết quả
            if results and len(results) > 0:
                result = results[0]

                if result.boxes is not None and len(result.boxes) > 0:
                    boxes = result.boxes.xyxy.cpu().numpy()  # [x1, y1, x2, y2]
                    confidences = result.boxes.conf.cpu().numpy()
                    class_ids = result.boxes.cls.cpu().numpy().astype(int)

                    for box, conf, cls_id in zip(boxes, confidences, class_ids):
                        # Lấy tên class
                        class_name = result.names[cls_id]
                        
                        detections.append({
                            "bbox": box.tolist(),
                            "confidence": float(conf),
                            "class_id": int(cls_id),
                            "class_name": class_name
                        })

            return detections

        except Exception as e:
            logger.error(f"Lỗi khi chạy detection: {e}")
            return []

    def draw_detections(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
        """
        Vẽ bounding boxes và labels lên frame

        Args:
            frame: Frame ảnh gốc
            detections: List các detection từ hàm detect()

        Returns:
            Frame đã được vẽ annotations
        """
        if not detections:
            return frame

        # Vẽ trực tiếp lên frame (tránh copy để giảm overhead)
        annotated_frame = frame

        for det in detections:
            try:
                # Lấy thông tin
                x1, y1, x2, y2 = [int(v) for v in det["bbox"]]
                confidence = det["confidence"]
                class_name = det["class_name"]

                # Lấy màu cho class
                color = COLORS_BY_CLASS.get(class_name, DEFAULT_COLOR)

                # Vẽ bounding box
                cv2.rectangle(
                    annotated_frame,
                    (x1, y1),
                    (x2, y2),
                    color,
                    settings.BBOX_THICKNESS
                )

                # Tạo label text (sử dụng tên tiếng Anh)
                label = f"{class_name} {confidence:.2f}"

                # Tính kích thước text để vẽ background
                (text_width, text_height), baseline = cv2.getTextSize(
                    label,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    settings.FONT_SCALE,
                    settings.FONT_THICKNESS
                )

                # Vẽ background cho text
                cv2.rectangle(
                    annotated_frame,
                    (x1, y1 - text_height - baseline - 5),
                    (x1 + text_width, y1),
                    color,
                    -1  # Filled
                )

                # Vẽ text
                cv2.putText(
                    annotated_frame,
                    label,
                    (x1, y1 - baseline - 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    settings.FONT_SCALE,
                    (255, 255, 255),
                    settings.FONT_THICKNESS,
                    cv2.LINE_AA
                )

            except Exception as e:
                logger.warning(f"Lỗi khi vẽ detection: {e}")
                continue

        return annotated_frame

    def detect_and_draw(self, frame: np.ndarray) -> tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Phát hiện và vẽ annotations lên frame trong một bước

        Args:
            frame: Frame ảnh gốc

        Returns:
            (annotated_frame, detections)
        """
        detections = self.detect(frame)
        annotated_frame = self.draw_detections(frame, detections)
        return annotated_frame, detections


# === SINGLETON INSTANCE ===
_detector_instance: Optional[YOLODetector] = None


def get_yolo_detector() -> YOLODetector:
    """
    Lấy instance singleton của YOLODetector
    """
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = YOLODetector()
    return _detector_instance

