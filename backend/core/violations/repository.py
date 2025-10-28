"""
Violation Repository - Lưu violations qua MongoDB API
"""

from typing import Dict, Any, Optional
from ...clients.mongodb_service import get_mongodb_service
from ...utils.logger import app_logger as logger


def save_violation_to_db(violation: Dict[str, Any], db=None) -> Optional[str]:
    """
    Lưu violation qua MongoDB API
    
    Args:
        violation: Violation record
        db: (ignored - compatibility only)
        
    Returns:
        Violation ID hoặc None nếu lỗi
    """
    try:
        service = get_mongodb_service()
        violation_id = service.create_violation(violation)
        return violation_id
        
    except Exception as e:
        logger.error(f"Lỗi lưu violation: {e}")
        return None
