"""
License Plate OCR - Wrapper gọi YOLO API Service
"""

import numpy as np
from typing import Optional
from ...clients.yolo_service import get_yolo_service
from ...utils.logger import app_logger as logger


def recognize_plate_text(plate_img: np.ndarray, conf_threshold: float = 0.25) -> Optional[str]:
    """
    OCR biển số via YOLO API
    
    Args:
        plate_img: Plate crop image (BGR)
        conf_threshold: Confidence threshold
        
    Returns:
        Plate text (e.g. "30A-12345") or None
    """
    try:
        service = get_yolo_service()
        plate_text = service.detect_plate(plate_img, conf=conf_threshold)
        
        if plate_text:
            logger.info(f"✓ OCR thành công: {plate_text}")
        else:
            logger.debug("OCR không nhận dạng được text")
        
        return plate_text
        
    except Exception as e:
        logger.error(f"Lỗi OCR biển số: {e}")
        return None
