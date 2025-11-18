"""
Stopline Detection API - Phát hiện vạch dừng từ ảnh
"""

import base64
import numpy as np
import cv2
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...core.analysis.stopline import detect_stop_line_with_fallback
from ...utils.image import center_crop_to_16_9
from ...utils.logger import app_logger as logger
from ..clients.mongodb_service import get_mongodb_service


router = APIRouter()


class DetectImagePayload(BaseModel):
    """Schema cho request detect stopline từ ảnh"""
    image: str  # Base64 hoặc Data URL
    camera_id: Optional[str] = None  # Nếu có, sẽ tự động lưu vào DB
    save_to_db: bool = False  # Tự động lưu regions vào DB


@router.post("/detection/stopline")
def detect_stopline_from_image(payload: DetectImagePayload):
    """
    Tự động phát hiện vạch dừng từ ảnh camera
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
        response = {"stopLine": None}

        if stopline_result:
            (x1, y1), (x2, y2) = stopline_result
            response["stopLine"] = [
                {"x": float(x1), "y": float(y1)},
                {"x": float(x2), "y": float(y2)},
            ]
            logger.info(f"✓ Phát hiện vạch dừng: {response['stopLine']}")
        else:
            logger.info("Không phát hiện được vạch dừng")

        # Tự động lưu vào DB nếu được yêu cầu
        if payload.save_to_db and payload.camera_id and response["stopLine"]:
            try:
                service = get_mongodb_service()
                regions = {}
                if response["stopLine"]:
                    regions["stopLine"] = response["stopLine"]

                success = service.update_camera_regions(payload.camera_id, regions)
                if success:
                    logger.info(f"✓ Đã lưu regions vào DB cho camera {payload.camera_id}")
                    response["saved_to_db"] = True
                else:
                    logger.warning(f"Không thể lưu regions cho camera {payload.camera_id}")
                    response["saved_to_db"] = False
            except Exception as e:
                logger.error(f"Lỗi khi lưu regions vào DB: {e}")
                response["saved_to_db"] = False

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi xử lý detect stopline: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")


class DetectPlatePayload(BaseModel):
    """Schema cho request detect plate từ vehicle crop image"""
    image: str  # Base64 hoặc Data URL của vehicle crop
    camera_id: Optional[str] = None  # Để lấy detection_rules


@router.post("/detection/plate")
def detect_plate_from_vehicle_crop(payload: DetectPlatePayload):
    """
    Tự động phát hiện và OCR biển số từ ảnh phương tiện (vehicle crop)
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
        vehicle_crop = cv2.imdecode(buffer, cv2.IMREAD_COLOR)

        if vehicle_crop is None:
            raise HTTPException(status_code=400, detail="Không thể giải mã ảnh")

        # Lấy minConfidence từ camera detection_rules (nếu có)
        min_confidence = None
        if payload.camera_id:
            try:
                service = get_mongodb_service()
                camera = service.get_camera(payload.camera_id)
                if camera and camera.get("detection_rules") and camera["detection_rules"].get("minConfidence"):
                    min_confidence = float(camera["detection_rules"]["minConfidence"])
            except Exception as e:
                logger.debug(f"Không lấy được detection_rules từ camera {payload.camera_id}: {e}")

        # Detect plate trên vehicle crop
        try:
            from ...core.detection.yolo import get_yolo_detector
            from ...core.license_plate.detector import recognize_plate_text
            from ...utils.image import encode_image_base64
            from ...config.config import settings

            detector = get_yolo_detector()

            # Fallback về settings nếu không có min_confidence từ camera
            if min_confidence is None:
                min_confidence = settings.YOLO_CONFIDENCE

            # Detect trực tiếp trên vehicle_crop (đã là crop rồi)
            crop_detections = detector.detect(vehicle_crop, conf=min_confidence)

            # Tìm license_plate trong detections
            plate_det = None
            for det in crop_detections:
                if det.get("class_name") == "license_plate":
                    plate_det = det
                    break

            if plate_det:
                # Crop plate từ vehicle crop
                plate_bbox = plate_det["bbox"]
                px1, py1, px2, py2 = map(int, plate_bbox)
                px1, py1 = max(0, px1), max(0, py1)
                px2, py2 = min(vehicle_crop.shape[1], px2), min(vehicle_crop.shape[0], py2)
                plate_crop = vehicle_crop[py1:py2, px1:px2]

                if plate_crop.size > 0:
                    # OCR biển số
                    plate_text = recognize_plate_text(plate_crop)

                    # Encode ảnh plate crop
                    plate_crop_b64 = encode_image_base64(plate_crop, quality=95)

                    logger.info(f"✓ Detect plate từ vehicle crop: {plate_text if plate_text else 'Không đọc được'}")

                    return {
                        "success": True,
                        "plate_text": plate_text,
                        "plate_crop": plate_crop_b64,
                        "bbox": plate_bbox
                    }
                else:
                    return {"success": False, "message": "Plate crop empty"}
            else:
                return {"success": False, "message": "Không detect được plate"}
        except Exception as e:
            logger.error(f"Lỗi khi detect plate: {e}")
            raise HTTPException(status_code=500, detail=f"Lỗi detect plate: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi xử lý detect plate: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")
