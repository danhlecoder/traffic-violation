"""
Traffic Violation Detection System - Backend API
"""

from fastapi import FastAPI

from .api.streams import router as streams_router
from .api.cameras import router as cameras_router
from .api.detection import router as detection_router
from .api.density import router as density_router
from .api.violations import router as violations_router
from .config.config import settings
from .api.lifecycle import lifespan
from .api.middleware import setup_cors


app = FastAPI(
    title="Traffic Violation Detection System",
    description="Backend API - Traffic violation detection using YOLO",
    version="1.0.0",
    lifespan=lifespan
)

setup_cors(app)


@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "1.0.0",
        "service": "Traffic Violation Detection"
    }


# Register routers
app.include_router(streams_router, tags=["Streaming"])
app.include_router(cameras_router, tags=["Cameras"])
app.include_router(detection_router, tags=["Detection"])
app.include_router(density_router, tags=["Density"])
app.include_router(violations_router, tags=["Violations"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
