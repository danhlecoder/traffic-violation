"""
Violations API - Endpoints cho quản lý vi phạm giao thông (Proxy to MongoDB API)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from ..clients.mongodb_service import get_mongodb_service
from ...utils.logger import app_logger as logger
import httpx
import asyncio


router = APIRouter()


@router.get("/violations")
def get_violations(
    camera_id: Optional[str] = Query(None, description="Filter theo camera ID"),
    status: Optional[str] = Query(None, description="Filter theo trạng thái"),
    limit: int = Query(10000, ge=1, le=50000, description="Số lượng tối đa (mặc định 10000 để lấy toàn bộ)"),
    offset: int = Query(0, ge=0, description="Offset phân trang")
):
    """
    Lấy danh sách phát hiện vi phạm giao thông (proxy to MongoDB API)
    """
    try:
        service = get_mongodb_service()
        violations = service.get_violations(
            status=status,
            camera_id=camera_id,
            limit=limit,
            offset=offset
        )

        logger.debug(f"Lấy {len(violations)} vi phạm")
        return {
            "success": True,
            "data": violations,
            "total": len(violations),
            "limit": limit,
            "offset": offset
        }

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


async def send_discord_notification(violation_data: dict):
    """
    Gửi thông báo vi phạm qua Discord webhook (N8N)
    """
    try:
        # URL production webhook (workflow phải được ACTIVATE trong N8N)
        # Test URL - chỉ dùng khi "Listen for test event" đang bật trong N8N UI
        webhook_url = "http://traffic_n8n:5678/webhook/violation-confirmed"
        # webhook_url = "http://traffic_n8n:5678/webhook/violation-confirmed"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook_url,
                json=violation_data
            )

            if response.status_code == 200:
                logger.info(f"Đã gửi Discord: {violation_data.get('track_id')}")
                return True
            else:
                logger.warning(f"Discord webhook failed: {response.status_code}")
                return False

    except Exception as e:
        logger.error(f"Lỗi gửi Discord: {e}")
        return False


@router.put("/violations/{track_id}")
async def update_violation(track_id: str, update_data: dict):
    """
    Cập nhật violation theo track_id (proxy to MongoDB API)
    Tự động gửi thông báo Discord khi status='confirmed'
    """
    try:
        service = get_mongodb_service()
        success = service.update_violation(track_id, update_data)

        if success:
            logger.debug(f"Cập nhật violation: track_id={track_id}")

            # Nếu update status thành 'confirmed', gửi thông báo Discord
            if update_data.get('status') == 'confirmed':
                try:
                    # Lấy thông tin đầy đủ của violation để gửi Discord
                    violation = service.get_violation(track_id)

                    if violation:
                        # Gửi Discord notification (không block response)
                        asyncio.create_task(send_discord_notification(violation))
                        logger.debug(f"Queue Discord notification: track_id={track_id}")

                except Exception as discord_error:
                    # Không làm fail toàn bộ request nếu Discord fail
                    logger.warning(f"Lỗi gửi Discord: {discord_error}")

            return {"success": True, "updated": track_id}
        else:
            raise HTTPException(status_code=404, detail="Violation not found or update failed")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi update violation: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")
