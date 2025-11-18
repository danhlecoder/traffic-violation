"""
Traffic Violation Detection System - Backend API v1
Hệ thống phát hiện vi phạm giao thông với YOLO + Tracking

API Endpoints Structure v1:
===========================

HEALTH:
  GET  /health                     - Kiểm tra trạng thái service
  
STREAMING (v1):
  GET  /v1/stream                  - MJPEG video stream với detection realtime
  GET  /v1/stream/density          - Mật độ phương tiện theo camera

CAMERAS (v1):
  GET    /v1/cameras               - Danh sách tất cả cameras
  POST   /v1/cameras               - Tạo hoặc cập nhật camera
  GET    /v1/cameras/{id}          - Chi tiết một camera
  PUT    /v1/cameras/{id}/regions  - Cập nhật ROI/stopline cho camera
  DELETE /v1/cameras/{id}          - Xóa camera

DETECTION (v1):
  POST /v1/detection/stopline      - Tự động phát hiện vạch dừng từ ảnh

VIOLATIONS (v1):
  GET /v1/violations               - Danh sách vi phạm (có filter)
  GET /v1/violations/{id}          - Chi tiết một vi phạm
  GET /v1/violations/stats         - Thống kê vi phạm theo thời gian
"""

from fastapi import FastAPI

from .api.v1.streams import router as streams_router
from .api.v1.cameras import router as cameras_router
from .api.v1.detection import router as detection_router
from .api.v1.violations import router as violations_router
from .config.config import settings
from .api.lifecycle import lifespan
from .api.middleware import setup_cors


app = FastAPI(
    title="Traffic Violation Detection System",
    description="Backend API v1 - Hệ thống phát hiện vi phạm giao thông",
    version="1.0.0",
    lifespan=lifespan
)

setup_cors(app)


@app.get("/health")
def health_check():
    """Kiểm tra trạng thái service"""
    return {
        "status": "ok",
        "version": "1.0.0",
        "api_version": "v1",
        "service": "Traffic Violation Detection Backend"
    }


# Đăng ký routers với prefix /v1
app.include_router(streams_router, prefix="/v1", tags=["Streaming"])
app.include_router(cameras_router, prefix="/v1", tags=["Cameras"])
app.include_router(detection_router, prefix="/v1", tags=["Detection"])
app.include_router(violations_router, prefix="/v1", tags=["Violations"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
