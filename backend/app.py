"""
Traffic Violation Detection System - Backend API
"""

from fastapi import FastAPI

from .api.streams import router as streams_router
from .api.cameras import router as cameras_router
from .api.density import router as density_router
from .core.config import settings
from .core.startup import lifespan
from .core.middleware import setup_cors


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
app.include_router(density_router, tags=["Density"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
