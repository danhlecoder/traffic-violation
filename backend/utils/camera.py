"""
Camera Schema - Pydantic models for camera configuration
"""

from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class CameraRegion(BaseModel):
    """Camera regions configuration (stopline, ROI)"""
    stopLine: Optional[List[dict]] = Field(None, description="Stopline [{'x': float, 'y': float}, ...]")
    lineB: Optional[List[dict]] = Field(None, description="LineB [{'x': float, 'y': float}, ...]")
    roi: Optional[List[dict]] = Field(None, description="ROI polygon [{'x': float, 'y': float}, ...]")


class Camera(BaseModel):
    """Camera configuration model - Accept 'url', 'rtsp', or 'rtsp_url'"""
    id: str = Field(..., description="Camera unique ID")
    name: str = Field(..., description="Camera name")
    rtsp: Optional[str] = Field(None, description="RTSP URL (alias for url)")
    url: Optional[str] = Field(None, description="RTSP/HTTP URL")
    rtsp_url: Optional[str] = Field(None, description="RTSP URL (alias)")
    location: Optional[str] = Field(None, description="Camera location")
    regions: Optional[CameraRegion] = Field(None, description="Configured regions")
    
    @field_validator('url', 'rtsp', 'rtsp_url', mode='before')
    def validate_url(cls, v, info):
        """Ensure at least one URL field is provided"""
        if v:
            return v
        # Check if any URL field has value
        data = info.data
        return data.get('url') or data.get('rtsp') or data.get('rtsp_url')
    
    def model_post_init(self, __context):
        """Normalize URL field after validation"""
        # Use first non-None value
        final_url = self.url or self.rtsp or self.rtsp_url
        if not final_url:
            raise ValueError("One of 'url', 'rtsp', or 'rtsp_url' must be provided")
        self.url = final_url
        self.rtsp = final_url
        self.rtsp_url = final_url
