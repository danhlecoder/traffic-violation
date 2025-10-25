"""
Violation Repository - Lưu violations vào database

Chức năng:
- Save violation records vào MongoDB
- Query violations
"""

from typing import Dict, Any, Optional

from ...utils.logger import app_logger as logger


def save_violation_to_db(violation: Dict[str, Any], db) -> Optional[str]:
    """
    Lưu violation vào MongoDB
    
    Args:
        violation: Violation record
        db: MongoDB database
        
    Returns:
        Violation ID hoặc None nếu lỗi
    """
    try:
        result = db.violations.insert_one(violation)
        return str(result.inserted_id)
        
    except Exception as e:
        logger.error(f"Lỗi lưu violation vào DB: {e}")
        return None
