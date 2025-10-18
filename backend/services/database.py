"""
Database Service - MongoDB connection management (singleton)
"""

from typing import Optional
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from ..core.config import settings
from ..utils.logger import app_logger as logger


# Singleton client
_client: Optional[MongoClient] = None


def get_client() -> MongoClient:
    """
    Lấy MongoDB client (singleton pattern)

    Returns:
        MongoClient instance
    """
    global _client

    if _client is None:
        try:
            uri = settings.mongo_uri
            _client = MongoClient(uri)
            _client.admin.command('ping')

        except Exception as e:
            logger.error(f"✗ Lỗi kết nối MongoDB: {e}")
            raise

    return _client


def get_db():
    """
    Lấy database instance

    Returns:
        Database object
    """
    client = get_client()
    db_name = settings.MONGO_DATABASE
    return client[db_name]


def init_indexes():
    """
    Khởi tạo các index cần thiết cho database

    Indexes:
    - cameras.id: unique index để đảm bảo không trùng ID camera
    """
    try:
        db = get_db()

        db.cameras.create_index('id', unique=True, name='uniq_camera_id')

    except PyMongoError as e:
        # Không crash app nếu tạo index thất bại
        logger.warning(f"Không thể tạo index: {e}")
    except Exception as e:
        logger.warning(f"Lỗi khi khởi tạo indexes: {e}")


def close_connection():
    """
    Đóng kết nối MongoDB (sử dụng khi shutdown app)
    """
    global _client

    if _client is not None:
        try:
            _client.close()
        except Exception as e:
            logger.error(f"MongoDB close error: {e}")
        finally:
            _client = None
