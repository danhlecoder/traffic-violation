"""
Schema cho Camera và Region
"""

from typing import Optional
from pydantic import BaseModel, Field


class Point(BaseModel):
    """Điểm tọa độ chuẩn hóa (0.0 - 1.0)"""
    x: float = Field(ge=0.0, le=1.0, description="Tọa độ X chuẩn hóa")
    y: float = Field(ge=0.0, le=1.0, description="Tọa độ Y chuẩn hóa")


class CameraRegion(BaseModel):
    """Vùng quan tâm trên camera"""
    stopLine: Optional[list[Point]] = Field(None, description="Vạch dừng (2 điểm)")
    lineB: Optional[list[Point]] = Field(None, description="Line B song song với stopLine")
    roi: Optional[list[Point]] = Field(None, description="Vùng quan tâm (danh sách điểm)")


class Camera(BaseModel):
    """Thông tin camera"""
    id: str = Field(..., description="ID duy nhất của camera")
    name: str = Field(..., description="Tên camera")
    rtsp: str = Field(..., description="URL RTSP của camera")
    location: str = Field(..., description="Vị trí lắp đặt camera")
    regions: Optional[CameraRegion] = Field(None, description="Các vùng đã cấu hình")
