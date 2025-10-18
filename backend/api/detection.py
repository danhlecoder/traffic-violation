"""
Stopline Detection API - Phát hiện vạch dừng từ ảnh
"""

import base64
import numpy as np
import cv2

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.stopline_detector import detect_stop_line_with_fallback, calculate_lineB_from_stopline, calculate_roi_from_lineB
from ..services.image_processing import center_crop_to_16_9
from ..utils.logger import app_logger as logger


router = APIRouter()


class DetectImagePayload(BaseModel):
    """Schema cho request detect stopline từ ảnh"""
    image: str  # Base64 hoặc Data URL


@router.post("/api/detect/stopline")
def detect_stopline_from_image(payload: DetectImagePayload):
    """
    Phát hiện vạch dừng từ ảnh base64
    
    Args:
        payload: Ảnh dạng base64 hoặc data URL
    
    Returns:
        dict: Kết quả phát hiện với stopLine, lineB, roi (normalized [0..1])
    """
    try:
        data = payload.image.strip()
        
        # Xử lý data URL
        if data.startswith("data:"):
            try:
                data = data.split(",", 1)[1]
            except Exception:
                raise HTTPException(status_code=400, detail="Data URL không hợp lệ")
        
        # Decode base64
        try:
            jpg_bytes = base64.b64decode(data, validate=False)
        except Exception:
            raise HTTPException(status_code=400, detail="Base64 không hợp lệ")
        
        # Decode image
        buffer = np.frombuffer(jpg_bytes, dtype=np.uint8)
        frame = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Không thể giải mã ảnh")
        
        # Xử lý ảnh: crop 16:9 và resize
        frame = center_crop_to_16_9(frame)
        
        try:
            frame = cv2.resize(frame, (1280, 720), interpolation=cv2.INTER_AREA)
        except Exception:
            pass
        
        # Downscale cho detection (tăng tốc độ)
        det_frame = frame
        try:
            det_frame = cv2.resize(frame, (960, 540), interpolation=cv2.INTER_AREA)
        except Exception:
            det_frame = frame
        
        # Chạy detection với logic fallback
        try:
            stopline_result = detect_stop_line_with_fallback(det_frame)
        except Exception as e:
            logger.exception(f"Lỗi khi phát hiện vạch dừng: {e}")
            stopline_result = None
        
        # Trả về kết quả
        response = {"stopLine": None, "lineB": None, "roi": None}
        
        if stopline_result:
            (x1, y1), (x2, y2) = stopline_result
            response["stopLine"] = [
                {"x": float(x1), "y": float(y1)},
                {"x": float(x2), "y": float(y2)},
            ]
            logger.info(f"✓ Phát hiện vạch dừng: {response['stopLine']}")
            
            # Tính lineB từ stopLine
            try:
                import os
                offset_px = int(os.getenv('LINE_B_OFFSET_PX', '64'))
                h, w = det_frame.shape[:2]
                lineB_result = calculate_lineB_from_stopline(stopline_result, h, offset_px=offset_px)
                (bx1, by1), (bx2, by2) = lineB_result
                response["lineB"] = [
                    {"x": float(bx1), "y": float(by1)},
                    {"x": float(bx2), "y": float(by2)},
                ]
                logger.info(f"✓ Tính lineB thành công: {response['lineB']}")
                
                # Tính ROI từ lineB
                try:
                    roi_result = calculate_roi_from_lineB(lineB_result)
                    response["roi"] = [{"x": float(px), "y": float(py)} for px, py in roi_result]
                    logger.info(f"✓ Tính ROI từ lineB: y_top={roi_result[0][1]:.3f}, points={len(response['roi'])}")
                except Exception as e:
                    logger.error(f"Lỗi khi tính ROI: {e}")
            
            except Exception as e:
                logger.error(f"Lỗi khi tính lineB: {e}")
        else:
            logger.info("Không phát hiện được vạch dừng")
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi xử lý detect stopline: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")
