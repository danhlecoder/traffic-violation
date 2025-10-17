"""
API Router - Vehicle Density
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any

from ..services.vehicle_density import get_vehicle_density_info, get_vehicle_count

router = APIRouter()


@router.get("/api/density/camera")
def get_camera_density(rtsp: str = Query(..., alias="src", description="URL RTSP của camera")) -> Dict[str, Any]:
    """
    Lấy mật độ phương tiện hiện tại của camera
    
    Args:
        rtsp: URL RTSP của camera
    
    Returns:
        Dict chứa thông tin mật độ của camera
        
    Example:
        GET /api/density/camera?src=rtsp://example.com/stream
        Response: {"count": 3, "level": "low", "description": "Thưa"}
    """
    try:
        vehicle_count = get_vehicle_count(rtsp)
        return get_vehicle_density_info(vehicle_count)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
