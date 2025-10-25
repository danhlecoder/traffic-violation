"""
Violation Schema - Pydantic models for violation records
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class ViolationImage(BaseModel):
    """Violation images (base64 encoded)"""
    full_frame: str = Field(..., description="Full frame base64")
    vehicle_crop: Optional[str] = Field(None, description="Vehicle crop base64")
    plate_crop: Optional[str] = Field(None, description="License plate crop base64")


class Violation(BaseModel):
    """Violation record model"""
    timestamp: datetime = Field(..., description="Violation timestamp")
    camera_id: str = Field(..., description="Camera ID")
    camera_name: Optional[str] = Field(None, description="Camera name")
    vehicle_type: str = Field(..., description="Vehicle type (car, motorcycle, bus, truck)")
    license_plate: Optional[str] = Field(None, description="License plate number")
    location: Optional[str] = Field(None, description="Camera location")
    bbox: List[float] = Field(..., description="Bounding box [x1, y1, x2, y2]")
    violation_type: str = Field(default="roi_entry", description="Violation type")
    status: str = Field(default="detected", description="Status: detected, confirmed, rejected")
    images: ViolationImage = Field(..., description="Violation images")
    confidence: float = Field(..., description="Detection confidence (0-1)")
    notes: Optional[str] = Field(None, description="Notes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-10-18T10:30:00",
                "camera_id": "cam-01",
                "camera_name": "Camera 1",
                "vehicle_type": "car",
                "bbox": [100, 200, 300, 400],
                "confidence": 0.95
            }
        }
