"""
YOLO API Service - Gọi YOLO Service Qua HTTP
"""

import base64
import cv2
import numpy as np
from typing import List, Dict, Any, Optional
from ..config.config import settings
from ..utils.logger import app_logger as logger
from .base_service import BaseAPIService


class YOLOService(BaseAPIService):
    """Service để gọi YOLO Detection API"""
    
    def __init__(self):
        super().__init__(
            base_url=settings.YOLO_API_URL,
            timeout=30,
            service_name="YOLO"
        )
    
    def detect_vehicle(self, frame: np.ndarray, conf: float = 0.5, iou: float = 0.4) -> List[Dict[str, Any]]:
        """
        Phát hiện xe, biển số, mũ bảo hiểm, đèn giao thông
        
        Args:
            frame: Ảnh BGR (numpy array)
            conf: Ngưỡng confidence
            iou: Ngưỡng IOU
            
        Returns:
            Danh sách detections: [{"bbox": [x1,y1,x2,y2], "confidence": 0.9, "class_name": "car"}, ...]
        """
        # Mã hóa frame sang base64
        _, buffer = cv2.imencode('.jpg', frame)
        img_b64 = base64.b64encode(buffer).decode('utf-8')
        
        # Gọi API
        payload = {"image": img_b64, "conf": conf, "iou": iou}
        result = self._post("/v1/detect/vehicle", payload)
        
        return result.get("detections", []) if result else []
    
    def detect_plate(self, plate_img: np.ndarray, conf: float = 0.35) -> Optional[str]:
        """
        OCR Biển Số Xe
        
        Args:
            plate_img: Ảnh biển số đã cắt (BGR)
            conf: Ngưỡng confidence
            
        Returns:
            Text biển số (ví dụ: "30A-12345") hoặc None
        """
        # Mã hóa sang base64
        _, buffer = cv2.imencode('.jpg', plate_img)
        img_b64 = base64.b64encode(buffer).decode('utf-8')
        
        # Gọi API
        payload = {"image": img_b64, "conf": conf}
        result = self._post("/v1/detect/plate", payload)
        
        return result.get("plate_text") if result else None


# Singleton
_yolo_service = None

def get_yolo_service() -> YOLOService:
    """Lấy YOLO service instance"""
    global _yolo_service
    if _yolo_service is None:
        _yolo_service = YOLOService()
    return _yolo_service
