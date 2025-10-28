"""
Logic Khởi Động/Tắt Ứng Dụng
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from ..config.config import settings
from ..clients.mongodb_service import get_mongodb_service
from ..clients.yolo_service import get_yolo_service
from ..utils.logger import app_logger as logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Quản lý Lifecycle: Kiểm tra các dịch vụ bên ngoài
    """
    # KHỞI ĐỘNG
    logger.info("🚀 Starting Traffic Violation Detection System (API Gateway)")
    
    # Kiểm tra MongoDB API
    try:
        mongodb_service = get_mongodb_service()
        if mongodb_service.health_check():
            logger.info("✓ MongoDB API connected")
        else:
            logger.warning("⚠ MongoDB API not available")
    except Exception as e:
        logger.warning(f"MongoDB API check failed: {e}")

    # Kiểm tra YOLO API
    try:
        yolo_service = get_yolo_service()
        if yolo_service.health_check():
            logger.info("✓ YOLO API connected")
        else:
            logger.warning("⚠ YOLO API not available")
    except Exception as e:
        logger.warning(f"YOLO API check failed: {e}")

    logger.info(f"✓ Backend ready at {settings.HOST}:{settings.PORT}")
    
    yield
    
    # TẮT
    logger.info("🛑 Shutting down backend")
