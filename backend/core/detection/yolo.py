"""
YOLO Detector - API Client Wrapper Cho Xử Lý Stream
"""

from typing import List, Dict, Any
import numpy as np
import cv2
from ...clients.yolo_service import get_yolo_service
from ...utils.logger import app_logger as logger


class YOLODetector:
    """YOLO Detector - Gọi YOLO API Service (chậm hơn nhưng phân tán)"""
    
    def __init__(self):
        self.service = get_yolo_service()
        logger.info("✓ YOLO Detector initialized (API mode)")
    
    def detect(self, frame: np.ndarray, conf: float = 0.5, iou: float = 0.4) -> List[Dict[str, Any]]:
        """
        Phát hiện qua YOLO API
        
        Returns:
            Danh sách detections: [{"bbox": [x1,y1,x2,y2], "confidence": 0.9, "class_name": "car"}, ...]
        """
        return self.service.detect_vehicle(frame, conf=conf, iou=iou)
    
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
            if track_id:
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
