"""
MongoDB API Service - Database Gateway
API v1 với connection pooling và indexes

API Endpoints:
  GET  /health                       - Kiểm tra trạng thái service

  CAMERAS:
  GET    /v1/cameras                 - Danh sách cameras
  POST   /v1/cameras                 - Tạo camera mới
  GET    /v1/cameras/{id}            - Chi tiết camera
  PUT    /v1/cameras/{id}            - Cập nhật camera
  DELETE /v1/cameras/{id}            - Xóa camera
  PUT    /v1/cameras/{id}/regions    - Cập nhật stopline

  VIOLATIONS:
  GET  /v1/violations                - Danh sách vi phạm
  POST /v1/violations                - Tạo vi phạm mới
"""

import os
import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, PyMongoError
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from fastapi import APIRouter
from datetime import datetime
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mongo-service")

app = FastAPI(
    title="MongoDB API Service",
    version="2.0.0",
    description="API v1 - MongoDB gateway với connection pooling"
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

# MongoDB client with connection pooling
_client = None
_db = None


def get_db():
    """Get MongoDB database with connection pooling"""
    global _client, _db
    if _db is None:
        mongo_host = os.getenv("MONGO_HOST", "mongo")
        mongo_port = int(os.getenv("MONGO_PORT", "27017"))
        mongo_db = os.getenv("MONGO_DATABASE", "traffic")
        mongo_user = os.getenv("MONGO_USER", "admin")
        mongo_pass = os.getenv("MONGO_PASSWORD", "admin123")

        connection_string = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:{mongo_port}/"

        # Connection pooling configuration
        _client = MongoClient(
            connection_string,
            maxPoolSize=50,              # Max connections in pool
            minPoolSize=10,              # Min connections to maintain
            maxIdleTimeMS=45000,         # Close idle connections after 45s
            waitQueueTimeoutMS=5000,     # Wait max 5s for connection
            serverSelectionTimeoutMS=5000,  # Server selection timeout
            connectTimeoutMS=10000,      # Connection timeout
            socketTimeoutMS=20000        # Socket operation timeout
        )
        _db = _client[mongo_db]
        logger.info(f"✓ Connected to MongoDB: {mongo_user}@{mongo_host}:{mongo_port}/{mongo_db}")
        logger.info(f"✓ Connection pool: maxPoolSize=50, minPoolSize=10")

    return _db


async def create_indexes():
    """Create database indexes for performance"""
    try:
        db = get_db()

        # Cameras collection indexes
        cameras = db["cameras"]
        cameras.create_index([("id", ASCENDING)], unique=True)
        cameras.create_index([("active", ASCENDING)])
        logger.info("✓ Created cameras indexes")

        # Violations collection indexes
        violations = db["violations"]
        violations.create_index([("timestamp", DESCENDING)])
        violations.create_index([("camera_id", ASCENDING), ("timestamp", DESCENDING)])
        violations.create_index([("status", ASCENDING), ("timestamp", DESCENDING)])
        violations.create_index([("license_plate", ASCENDING)])
        logger.info("✓ Created violations indexes")

    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")


@app.on_event("startup")
async def startup():
    """Connect to MongoDB and create indexes on startup"""
    get_db()
    await create_indexes()
    logger.info("🚀 MongoDB API Service ready!")


@app.get("/health")
async def health():
    """Health check"""
    try:
        db = get_db()
        db.command("ping")
        return {"status": "ok", "mongodb": "connected"}
    except Exception as e:
        return {"status": "error", "mongodb": str(e)}


# ===================== CAMERAS =====================

class Camera(BaseModel):
    id: str
    name: str
    rtsp: str  # Bắt buộc - URL RTSP stream
    location: Optional[str] = None
    active: Optional[bool] = True
    regions: Optional[Dict] = None  # {stopLine: [...]}


@router_v1.get("/cameras")
async def get_cameras():
    """Lấy danh sách tất cả cameras"""
    try:
        db = get_db()
        cameras = list(db.cameras.find({}, {"_id": 0}))
        return {"success": True, "cameras": cameras}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_v1.get("/cameras/{camera_id}")
async def get_camera(camera_id: str):
    """Get camera by ID"""
    try:
        db = get_db()
        camera = db.cameras.find_one({"id": camera_id}, {"_id": 0})
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")
        return {"success": True, "camera": camera}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_v1.post("/cameras")
async def create_camera(camera: Dict[str, Any]):
    """Create new camera (accept any dict)"""
    try:
        db = get_db()
        camera["created_at"] = datetime.utcnow()

        # Upsert based on id
        camera_id = camera.get("id")
        if camera_id:
            db.cameras.update_one(
                {"id": camera_id},
                {"$set": camera},
                upsert=True
            )
            return {"success": True, "id": camera_id}
        else:
            result = db.cameras.insert_one(camera)
            return {"success": True, "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_v1.put("/cameras/{camera_id}")
async def update_camera(camera_id: str, camera_data: Dict[str, Any]):
    """Update camera by ID (replace entire document)"""
    try:
        db = get_db()

        # Ensure id matches
        camera_data["id"] = camera_id

        # Remove fields we don't want to update
        camera_data.pop("_id", None)
        camera_data.pop("created_at", None)  # Keep original created_at

        result = db.cameras.replace_one(
            {"id": camera_id},
            camera_data,
            upsert=False
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Camera not found")

        return {"success": True, "updated": camera_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_v1.delete("/cameras/{camera_id}")
async def delete_camera(camera_id: str):
    """Delete camera by ID"""
    try:
        db = get_db()
        result = db.cameras.delete_one({"id": camera_id})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Camera not found")

        return {"success": True, "deleted": camera_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_v1.put("/cameras/{camera_id}/regions")
async def update_camera_regions(camera_id: str, regions: Dict[str, Any]):
    """Update camera regions (ROI, stopLine)"""
    try:
        db = get_db()

        # Update regions field
        result = db.cameras.update_one(
            {"id": camera_id},
            {"$set": {"regions": regions}}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Camera not found")

        return {"success": True, "updated": camera_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_v1.put("/cameras/{camera_id}/detection-rules")
async def update_camera_detection_rules(camera_id: str, rules: Dict[str, Any]):
    """Update camera detection rules"""
    try:
        db = get_db()

        # Update detection_rules field
        result = db.cameras.update_one(
            {"id": camera_id},
            {"$set": {"detection_rules": rules}}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Camera not found")

        return {"success": True, "updated": camera_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===================== VIOLATIONS =====================

class Violation(BaseModel):
    timestamp: str
    camera_id: str
    camera_name: str
    location: str
    vehicle_type: str
    license_plate: Optional[str] = None
    violation_tags: List[str]  # List các loại vi phạm thay vì violation_type
    violation_history: Optional[List[Dict]] = None  # Lịch sử vi phạm
    status: str = "detected"
    images: Dict
    confidence: float
    track_id: Optional[str] = None  # Track ID string (format: 5 ký tự alphanumeric + hhmmss)
    speed: Optional[float] = None  # Tốc độ tính bằng km/h


@router_v1.get("/violations")
async def get_violations(
    status: Optional[str] = None,
    camera_id: Optional[str] = None,
    limit: int = 10000,  # Tăng limit mặc định để lấy toàn bộ violations
    offset: int = 0
):
    """Get violations with filters"""
    try:
        db = get_db()

        # Build query
        query = {}
        if status:
            query["status"] = status
        if camera_id:
            query["camera_id"] = camera_id

        # Query with pagination
        violations = list(
            db.violations.find(query)
            .sort("timestamp", -1)
            .skip(offset)
            .limit(limit)
        )

        # Convert _id to id for frontend
        for v in violations:
            if "_id" in v:
                v["id"] = str(v["_id"])
                del v["_id"]

        total = db.violations.count_documents(query)

        return {
            "success": True,
            "data": violations,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_v1.post("/violations")
async def create_violation(violation: Violation):
    """Create new violation"""
    try:
        db = get_db()
        violation_dict = violation.dict()

        result = db.violations.insert_one(violation_dict)
        return {"success": True, "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_v1.get("/violations/{track_id}")
async def get_violation_by_track_id(track_id: str):
    """Lấy violation theo track_id"""
    try:
        db = get_db()
        violation = db.violations.find_one({"track_id": track_id}, {"_id": 0})
        if not violation:
            raise HTTPException(status_code=404, detail=f"Violation not found with track_id: {track_id}")
        return {"success": True, "violation": violation}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_v1.put("/violations/{track_id}")
async def update_violation_by_track_id(track_id: str, update_data: Dict[str, Any]):
    """Update violation by track_id"""
    try:
        db = get_db()

        # Chỉ cho phép update các field được chỉnh sửa
        allowed_fields = [
            "violation_tags",  # Chỉ dùng violation_tags
            "violation_history",  # Lịch sử vi phạm
            "vehicle_type",
            "license_plate",
            "status",
            "timestamp",
            "speed",
            "images",
        ]
        update_dict = {k: v for k, v in update_data.items() if k in allowed_fields}

        if not update_dict:
            raise HTTPException(status_code=400, detail="No valid fields to update")

        # Tìm violation theo track_id (không cần filter status để có thể update cả confirmed/skipped)
        result = db.violations.update_one(
            {"track_id": track_id},  # Tìm theo track_id, không filter status
            {"$set": update_dict}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail=f"Violation not found with track_id: {track_id}")

        return {"success": True, "updated": track_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Đăng ký router v1
app.include_router(router_v1, tags=["Database v1"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
