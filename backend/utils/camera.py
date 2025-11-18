"""
Camera Schema - Pydantic models for camera configuration
"""

from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class CameraRegion(BaseModel):
    """Camera regions configuration (stopline only)"""
    stopLine: Optional[List[dict]] = Field(None, description="Stopline [{'x': float, 'y': float}, ...]")
    lineB: Optional[List[dict]] = Field(None, description="Line B song song với stopline, cách 1m (ppm) về phía trên")


class Camera(BaseModel):
    """Camera configuration model - Only use 'rtsp' field"""
    id: str = Field(..., description="Camera unique ID")
    name: str = Field(..., description="Camera name")
    rtsp: str = Field(..., description="RTSP URL")
    location: Optional[str] = Field(None, description="Camera location")
    regions: Optional[CameraRegion] = Field(None, description="Configured regions")

    @field_validator('rtsp')
    def validate_rtsp(cls, v):
        """Ensure RTSP URL is provided"""
        if not v or not v.strip():
            raise ValueError("RTSP URL is required")
        return v.strip()
