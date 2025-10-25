"""
Logger - Cấu hình logging cho ứng dụng
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from ..config.config import settings


def _create_logger(name: str) -> logging.Logger:
    """
    Tạo logger với cấu hình từ settings

    Args:
        name: Tên của logger

    Returns:
        Logger instance đã được cấu hình
    """
    logger = logging.getLogger(name)

    # Set level từ config
    level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
    logger.setLevel(level)

    # Tạo console handler nếu chưa có
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        console_handler = logging.StreamHandler()
        console_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        console_handler.setFormatter(logging.Formatter(console_format))
        logger.addHandler(console_handler)

    # Không propagate để tránh duplicate logs
    logger.propagate = False

    return logger


def _ensure_file_handler(logger: logging.Logger) -> None:
    """
    Thêm file handler (rotating) cho logger

    Args:
        logger: Logger instance
    """
    log_file = settings.LOG_FILE

    # Tạo thư mục logs nếu chưa có
    try:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Nếu không tạo được thư mục, chỉ log ra console
        return

    # Kiểm tra xem đã có handler cho file này chưa
    for handler in logger.handlers:
        if isinstance(handler, RotatingFileHandler):
            base = getattr(handler, "baseFilename", None)
            if base and os.path.abspath(base) == os.path.abspath(log_file):
                return

    # Tạo rotating file handler
    try:
        max_bytes = settings.LOG_MAX_BYTES
        backup_count = settings.LOG_BACKUP_COUNT

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )

        file_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        file_handler.setFormatter(logging.Formatter(file_format))

        logger.addHandler(file_handler)

    except Exception as e:
        # Best effort, nếu không tạo được file handler thì thôi
        print(f"Không thể tạo file handler: {e}")


# === Tạo các logger chính ===
app_logger = _create_logger("traffic.app")
stream_logger = _create_logger("traffic.stream")
detector_logger = _create_logger("traffic.detector")

# Thêm file handlers
for logger_instance in [app_logger, stream_logger, detector_logger]:
    _ensure_file_handler(logger_instance)

# Cấu hình cho các logger của thư viện
for lib_logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"]:
    try:
        lib_logger = logging.getLogger(lib_logger_name)
        _ensure_file_handler(lib_logger)
    except Exception:
        pass
