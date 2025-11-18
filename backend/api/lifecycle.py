"""
Logic Khởi Động/Tắt Ứng Dụng
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from ..config.config import settings
from .clients.mongodb_service import get_mongodb_service
from ..utils.logger import app_logger as logger
from ..core.events.violation_broker import get_violation_event_broker


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Quản lý Lifecycle: Kiểm tra các dịch vụ bên ngoài
    """
    # KHỞI ĐỘNG
    logger.info("🚀 Starting Traffic Violation Detection System")

    # Kiểm tra MongoDB API
    try:
        mongodb_service = get_mongodb_service()
        if mongodb_service.health_check():
            logger.info("✓ MongoDB API connected")
        else:
            logger.warning("⚠ MongoDB API not available")
    except Exception as e:
        logger.warning(f"MongoDB API check failed: {e}")

    loop = asyncio.get_running_loop()
    get_violation_event_broker().set_loop(loop)
    logger.info("✓ Violation event broker attached to event loop")

    logger.info(f"✓ Backend ready at {settings.HOST}:{settings.PORT}")

    yield

    # TẮT
    logger.info("🛑 Shutting down backend")
