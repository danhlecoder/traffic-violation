"""
YOLO Service - Phát Hiện Phương Tiện + Nhận Dạng Biển Số
API v1 với async processing và error handling

API Endpoints:
  GET  /health                    - Kiểm tra trạng thái service
  POST /v1/detect/vehicle         - Phát hiện xe, biển số, mũ bảo hiểm
  POST /v1/detect/plate           - Nhận dạng text biển số (OCR)
"""

import os
import cv2
import numpy as np
import statistics
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from ultralytics import YOLO
from typing import List, Dict, Any, Optional
from fastapi import APIRouter
import base64
import logging
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("yolo-service")

# Thread pool cho CPU-bound operations
executor = ThreadPoolExecutor(max_workers=2)

app = FastAPI(
    title="YOLO Detection Service",
    version="2.0.0",
    description="API v1 - Dịch vụ phát hiện đối tượng với YOLO"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router cho API v1
router_v1 = APIRouter(prefix="/v1")

# Models
_vehicle_model = None
_plate_model = None

# Allowed chars for license plate
ALLOWED_CHARS = ['0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F','G','H','K','L','M','N','P','S','T','U','V','X','Y','Z']


async def load_vehicle_model():
    """Load vehicle detection model asynchronously"""
    global _vehicle_model
    if _vehicle_model is None:
        path = os.getenv("VEHICLE_MODEL_PATH", "/app/models/best1.pt")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Vehicle model not found: {path}")
        
        # Load in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        _vehicle_model = await loop.run_in_executor(executor, YOLO, path)
        logger.info(f"✓ Vehicle model loaded: {path}")
    return _vehicle_model


async def load_plate_model():
    """Load license plate OCR model asynchronously"""
    global _plate_model
    if _plate_model is None:
        path = os.getenv("PLATE_MODEL_PATH", "/app/models/license_plate.pt")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Plate model not found: {path}")
        
        # Load in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        _plate_model = await loop.run_in_executor(executor, YOLO, path)
        logger.info(f"✓ Plate model loaded: {path}")
    return _plate_model


@app.on_event("startup")
async def startup():
    """Load models on startup in parallel"""
    try:
        logger.info("Loading models...")
        await asyncio.gather(
            load_vehicle_model(),
            load_plate_model()
        )
        logger.info("🚀 YOLO Service ready!")
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        raise


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "ok",
        "models": {
            "vehicle": _vehicle_model is not None,
            "plate": _plate_model is not None
        }
    }


class DetectRequest(BaseModel):
    """Request schema for detection"""
    image: str = Field(..., description="Base64 encoded image")
    conf: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence threshold")
    iou: float = Field(default=0.4, ge=0.0, le=1.0, description="IOU threshold")
    max_det: int = Field(default=50, ge=1, le=300, description="Max detections")


class DetectionResponse(BaseModel):
    """Standardized response format"""
    success: bool
    detections: List[Dict[str, Any]]
    count: int
    error: Optional[str] = None


def _run_detection(model, img, conf, iou, max_det):
    """CPU-bound detection in thread pool"""
    return model.predict(
        source=img,
        conf=conf,
        iou=iou,
        max_det=max_det,
        verbose=False
    )


@router_v1.post("/detect/vehicle", response_model=DetectionResponse)
async def detect_vehicle(request: DetectRequest):
    """
    Phát hiện xe, biển số, mũ bảo hiểm, đèn giao thông (async)
    Returns: Standardized detection response
    """
    try:
        # Decode base64
        img_b64 = request.image
        if img_b64.startswith("data:image"):
            img_b64 = img_b64.split(",")[1]
        
        img_bytes = base64.b64decode(img_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return DetectionResponse(
                success=False,
                detections=[],
                count=0,
                error="Invalid image format"
            )
        
        # Get model
        model = await load_vehicle_model()
        
        # Run detection in thread pool (CPU-bound)
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            executor,
            _run_detection,
            model, img, request.conf, request.iou, request.max_det
        )
        
        # Parse results
        detections = []
        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None and len(result.boxes) > 0:
                boxes = result.boxes.xyxy.cpu().numpy()
                confs = result.boxes.conf.cpu().numpy()
                classes = result.boxes.cls.cpu().numpy().astype(int)
                
                names = model.names
                if isinstance(names, dict):
                    class_names = {int(k): v for k, v in names.items()}
                else:
                    class_names = {i: n for i, n in enumerate(names)}
                
                for box, conf, cls in zip(boxes, confs, classes):
                    x1, y1, x2, y2 = box
                    detections.append({
                        "bbox": [float(x1), float(y1), float(x2), float(y2)],
                        "confidence": float(conf),
                        "class_id": int(cls),
                        "class_name": class_names.get(int(cls), f"class_{cls}")
                    })
        
        return DetectionResponse(
            success=True,
            detections=detections,
            count=len(detections)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detection error: {e}")
        return DetectionResponse(
            success=False,
            detections=[],
            count=0,
            error=str(e)
        )


@router_v1.post("/detect/plate")
async def detect_plate(request: DetectRequest):
    """
    Nhận dạng text biển số xe (OCR)
    Returns: Text biển số (format XX-XXXXX)
    """
    try:
        # Decode base64
        img_b64 = request.image
        if img_b64.startswith("data:image"):
            img_b64 = img_b64.split(",")[1]
        
        img_bytes = base64.b64decode(img_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image")
        
        # Preprocess (simple version, no heavy CV)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        gray_eq = clahe.apply(gray)
        yolo_input = cv2.cvtColor(gray_eq, cv2.COLOR_GRAY2BGR)
        
        # Run detection
        model = await load_plate_model()
        results = model.predict(
            source=yolo_input,
            conf=request.conf if request.conf > 0 else 0.35,
            iou=request.iou if request.iou > 0 else 0.6,
            verbose=False
        )
        
        # Parse results
        boxes, labels = [], []
        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None and len(result.boxes) > 0:
                xyxy = result.boxes.xyxy.cpu().numpy()
                cls = result.boxes.cls.cpu().numpy().astype(int)
                
                names = model.names
                if isinstance(names, dict):
                    idx_to_name = {int(k): v for k, v in names.items()}
                else:
                    idx_to_name = {i: n for i, n in enumerate(names)}
                
                for (x1, y1, x2, y2), c in zip(xyxy, cls):
                    name = idx_to_name.get(int(c), None)
                    if name in ALLOWED_CHARS:
                        boxes.append([float(x1), float(y1), float(x2), float(y2)])
                        labels.append(name)
        
        # Sort into 2 rows
        plate_text = ""
        if boxes:
            rows = sort_boxes_two_rows(boxes)
            row_texts = ["".join([labels[k] for k in row]) for row in rows]
            plate_text = "-".join(row_texts)
        
        return {
            "success": True,
            "plate_text": plate_text if plate_text else None,
            "characters": len(labels)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def sort_boxes_two_rows(boxes_xyxy: List[List[float]]) -> List[List[int]]:
    """Sort character boxes into 2 rows (Vietnam license plate format)"""
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


# Đăng ký router v1
app.include_router(router_v1, tags=["Detection v1"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
