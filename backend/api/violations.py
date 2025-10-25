"""
Violations API - Endpoints cho quản lý vi phạm giao thông

Endpoints:
- GET /api/violations: Lấy danh sách vi phạm
- GET /api/violations/{id}: Lấy chi tiết vi phạm
- GET /api/violations/stats: Thống kê vi phạm
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException
from bson import ObjectId

from ..utils.database import get_db
from ..utils.violation import Violation
from ..utils.logger import app_logger as logger


router = APIRouter()


@router.get("/api/violations")
def get_violations(
    camera_id: Optional[str] = Query(None, description="Filter theo camera ID"),
    vehicle_type: Optional[str] = Query(None, description="Filter theo loại xe"),
    status: Optional[str] = Query(None, description="Filter theo trạng thái"),
    from_date: Optional[str] = Query(None, description="Từ ngày (ISO format)"),
    to_date: Optional[str] = Query(None, description="Đến ngày (ISO format)"),
    limit: int = Query(50, ge=1, le=500, description="Số lượng tối đa"),
    offset: int = Query(0, ge=0, description="Offset phân trang")
):
    """
    Lấy danh sách vi phạm giao thông
    """
    try:
        db = get_db()

        # Build query filter
        query_filter = {}

        if camera_id:
            query_filter["camera_id"] = camera_id

        if vehicle_type:
            query_filter["vehicle_type"] = vehicle_type

        if status:
            query_filter["status"] = status

        # Date range
        if from_date or to_date:
            date_filter = {}
            if from_date:
                try:
                    from_dt = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
                    date_filter["$gte"] = from_dt
                except:
                    raise HTTPException(status_code=400, detail="Invalid from_date format")

            if to_date:
                try:
                    to_dt = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
                    date_filter["$lte"] = to_dt
                except:
                    raise HTTPException(status_code=400, detail="Invalid to_date format")

            if date_filter:
                query_filter["timestamp"] = date_filter

        # Count total
        total = db.violations.count_documents(query_filter)

        # Query with pagination
        cursor = db.violations.find(query_filter).sort("timestamp", -1).skip(offset).limit(limit)

        # Convert to list
        violations = []
        for doc in cursor:
            # Convert ObjectId to string
            doc["id"] = str(doc.pop("_id"))
            violations.append(doc)

        logger.info(f"Lấy {len(violations)}/{total} vi phạm")

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "data": violations
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi get violations: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")


@router.get("/api/violations/{violation_id}")
def get_violation_detail(violation_id: str):
    """
    Lấy chi tiết một vi phạm
    """
    try:
        db = get_db()

        # Convert to ObjectId
        try:
            oid = ObjectId(violation_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid violation ID")

        # Find
        doc = db.violations.find_one({"_id": oid})

        if not doc:
            raise HTTPException(status_code=404, detail="Violation not found")

        # Convert ObjectId to string
        doc["id"] = str(doc.pop("_id"))

        return doc

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi get violation detail: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")


@router.get("/api/violations/stats/summary")
def get_violations_stats(
    camera_id: Optional[str] = Query(None, description="Filter theo camera ID"),
    days: int = Query(7, ge=1, le=365, description="Số ngày gần đây")
):
    """
    Thống kê vi phạm
    """
    try:
        db = get_db()

        # Date range (Vietnam timezone UTC+7)
        vietnam_tz = timezone(timedelta(hours=7))
        from_date = datetime.now(vietnam_tz) - timedelta(days=days)

        # Base filter
        base_filter = {"timestamp": {"$gte": from_date}}
        if camera_id:
            base_filter["camera_id"] = camera_id

        # Total
        total = db.violations.count_documents(base_filter)

        # By vehicle type
        pipeline_vehicle = [
            {"$match": base_filter},
            {"$group": {"_id": "$vehicle_type", "count": {"$sum": 1}}}
        ]
        by_vehicle = {doc["_id"]: doc["count"] for doc in db.violations.aggregate(pipeline_vehicle)}

        # By status
        pipeline_status = [
            {"$match": base_filter},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        by_status = {doc["_id"]: doc["count"] for doc in db.violations.aggregate(pipeline_status)}

        # By camera (nếu không filter camera)
        by_camera = {}
        if not camera_id:
            pipeline_camera = [
                {"$match": base_filter},
                {"$group": {"_id": "$camera_id", "count": {"$sum": 1}}}
            ]
            by_camera = {doc["_id"]: doc["count"] for doc in db.violations.aggregate(pipeline_camera)}

        return {
            "total": total,
            "by_vehicle_type": by_vehicle,
            "by_status": by_status,
            "by_camera": by_camera,
            "period_days": days
        }

    except Exception as e:
        logger.error(f"Lỗi get violations stats: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")
