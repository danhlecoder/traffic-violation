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
from ..core.violations.async_processor import get_async_processor, shutdown_async_processor


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

    # Khởi động Async Violation Processor (xử lý vi phạm background để tránh lag stream)
    try:
        processor = get_async_processor()
        logger.info("✓ Async violation processor started")
    except Exception as e:
        logger.warning(f"⚠ Async processor failed to start: {e}")

    logger.info(f"✓ Backend ready at {settings.HOST}:{settings.PORT}")

    yield

    # TẮT
    logger.info("🛑 Shutting down backend")

    # Shutdown Async Violation Processor (đợi xử lý hết queue trước khi tắt)
    try:
        shutdown_async_processor()
        logger.info("✓ Async violation processor stopped")
    except Exception as e:
        logger.warning(f"⚠ Async processor shutdown error: {e}")
