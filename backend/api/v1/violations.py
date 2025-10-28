"""
Violations API - Endpoints cho quản lý vi phạm giao thông (Proxy to MongoDB API)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Query, HTTPException

from ...clients.mongodb_service import get_mongodb_service
from ...utils.logger import app_logger as logger


router = APIRouter()


@router.get("/violations")
def get_violations(
    camera_id: Optional[str] = Query(None, description="Filter theo camera ID"),
    status: Optional[str] = Query(None, description="Filter theo trạng thái"),
    limit: int = Query(50, ge=1, le=500, description="Số lượng tối đa"),
    offset: int = Query(0, ge=0, description="Offset phân trang")
):
    """
    Lấy danh sách phát hiện vi phạm giao thông (proxy to MongoDB API)
    """
    try:
        service = get_mongodb_service()
        result = service.get_violations(
            status=status,
            camera_id=camera_id,
            limit=limit,
            offset=offset
        )
        
        logger.info(f"Lấy {len(result.get('data', []))}/{result.get('total', 0)} phát hiện")
        return result

    except Exception as e:
        logger.error(f"Lỗi get violations: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")


@router.get("/violations/{violation_id}")
def get_violation_detail(violation_id: str):
    """
    Lấy chi tiết một vi phạm theo ID
    """
    raise HTTPException(status_code=501, detail="Not implemented yet - use MongoDB API directly")


@router.get("/violations/stats")
def get_violations_stats(
    camera_id: Optional[str] = Query(None, description="Filter theo camera ID"),
    days: int = Query(7, ge=1, le=365, description="Số ngày gần đây")
):
    """
    Lấy thống kê vi phạm theo camera và thời gian: implement in MongoDB API)
    """
    raise HTTPException(status_code=501, detail="Not implemented yet - use MongoDB API directly")
