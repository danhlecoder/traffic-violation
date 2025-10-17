"""
Application Startup/Shutdown Logic
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from .config import settings
from ..services.database import init_indexes, close_connection
from ..services.detector import get_yolo_detector
from ..utils.logger import app_logger as logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager: Khởi tạo và dọn dẹp tài nguyên
    """
    # STARTUP
    logger.info("🚀 Starting Traffic Violation Detection System")
    
    try:
        init_indexes()
        logger.info("✓ Database ready")
    except Exception as e:
        logger.error(f"Database init failed: {e}")

    try:
        get_yolo_detector()
        logger.info("✓ YOLO detector ready")
    except Exception as e:
        logger.warning(f"YOLO init failed: {e}")

    logger.info(f"✓ Server ready at {settings.HOST}:{settings.PORT}")
    
    yield
    
    # SHUTDOWN
    logger.info("🛑 Shutting down server")
    try:
        close_connection()
        logger.info("✓ Database closed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
