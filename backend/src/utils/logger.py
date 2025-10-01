import logging
import os
from logging.handlers import RotatingFileHandler


def _create_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, level, logging.INFO))

    # Always ensure a console handler exists (one-time)
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        handler = logging.StreamHandler()
        fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)

    # Prevent double logging to root
    logger.propagate = False
    return logger


def _ensure_file_handler(logger: logging.Logger) -> None:
    """Attach a rotating file handler to the given logger if not present."""
    log_file = os.getenv("LOG_FILE", "/app/logs/backend.log")
    try:
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
    except Exception:
        # Best-effort; fallback to console only if cannot create dir
        return

    # Avoid adding duplicate handlers to the same file
    for h in logger.handlers:
        base = getattr(h, "baseFilename", None)
        if base and os.path.abspath(base) == os.path.abspath(log_file):
            return

    max_bytes = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB
    backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    fh = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")
    fh.setFormatter(logging.Formatter(fmt))
    logger.addHandler(fh)


app_logger = _create_logger("traffic.app")
stream_logger = _create_logger("traffic.stream")

# Attach file logging to our loggers and common web server loggers
for _name in ("traffic.app", "traffic.stream", "uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
    try:
        _ensure_file_handler(logging.getLogger(_name))
    except Exception:
        pass


