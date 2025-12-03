"""
Violation Repository - Lưu trữ và truy vấn vi phạm
"""

from typing import Dict, Any, Optional, List
from ...api.clients.mongodb_service import get_mongodb_service
from ...utils.logger import app_logger as logger


VIOLATION_PRIORITY = {
    "detected": 0,
    "stopline_crossing": 1,
    "speed_violation": 2,
    "red_light": 3,
    "no_helmet": 2,
}


def _sort_tags(tags: List[str]) -> List[str]:
    """
    Sắp xếp và làm sạch tags:
    - Loại bỏ trùng lặp
    - Tự động gỡ 'detected' nếu có vi phạm thực sự khác
    - Sắp xếp theo độ ưu tiên
    """
    unique = []
    seen = set()
    for tag in tags:
        if tag and tag not in seen:
            seen.add(tag)
            unique.append(tag)

    # Tự động gỡ 'detected' nếu có vi phạm khác
    has_real_violation = any(t != "detected" for t in unique)
    if has_real_violation and "detected" in unique:
        unique.remove("detected")

    unique.sort(key=lambda t: VIOLATION_PRIORITY.get(t, 0), reverse=True)
    return unique


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
        track_id = violation.get('track_id')

        # Gửi track_id string trực tiếp đến MongoDB API (không convert sang int)
        service = get_mongodb_service()
        violation_id = service.save_violation(violation)

        if violation_id:
            logger.info(f"Đã lưu violation: ID={violation_id}, track_id={track_id}")
        else:
            logger.error(f"Lỗi lưu violation: track_id={track_id}")

        return violation_id

    except Exception as e:
        logger.error(f"Lỗi lưu violation: {e}")
        return None


def _build_history_entry(violation: Dict[str, Any]) -> Dict[str, Any]:
    """Tạo entry cho violation history từ violation_tags"""
    # Lấy type từ violation_tags (ưu tiên) hoặc fallback về violation_type
    tags = violation.get("violation_tags", [])
    violation_type = tags[0] if tags else violation.get("violation_type")

    return {
        "type": violation_type,
        "timestamp": violation.get("timestamp"),
        "speed": violation.get("speed"),
    }


def delete_violation_record(track_id: str) -> bool:
    """
    XÓA TOÀN BỘ violation record theo track_id
    ⚠️ WARNING: Chỉ dùng khi cần xóa hoàn toàn, không dùng để xóa tag riêng lẻ

    Args:
        track_id: Track ID của phương tiện

    Returns:
        True nếu xóa thành công, False nếu lỗi
    """
    try:
        if not track_id:
            logger.error("Không có track_id để xóa")
            return False

        service = get_mongodb_service()

        # Kiểm tra xem có tồn tại không
        try:
            existing = service.get_violation(track_id)
            if not existing:
                logger.debug(f"Không tìm thấy violation với track_id={track_id}")
                return False
        except Exception:
            return False

        # Xóa qua MongoDB service
        result = service.delete_violation(track_id)
        if result:
            logger.info(f"✅ Đã xóa violation: track_id={track_id}")
            return True
        else:
            logger.warning(f"⚠️ Không xóa được violation: track_id={track_id}")
            return False

    except Exception as e:
        logger.error(f"❌ Lỗi xóa violation track_id={track_id}: {e}")
        return False


def remove_violation_tag(track_id: str, tag_to_remove: str) -> bool:
    """
    XÓA 1 TAG cụ thể khỏi violation_tags, GIỮ NGUYÊN các tags khác

    Ví dụ: remove_violation_tag(track_id, "red_light")
    - violation_tags = ["red_light", "stopline_crossing"]
    → violation_tags = ["stopline_crossing"]

    Args:
        track_id: Track ID của phương tiện
        tag_to_remove: Tag cần xóa (vd: "red_light", "speed_violation")

    Returns:
        True nếu xóa thành công hoặc violation không tồn tại
        False nếu có lỗi
    """
    try:
        service = get_mongodb_service()

        # Lấy violation hiện tại
        existing = service.get_violation(track_id)
        if not existing:
            return True  # Không tồn tại → coi như đã xóa

        # Lấy tags hiện tại
        current_tags = existing.get("violation_tags", [])
        if tag_to_remove not in current_tags:
            return True  # Tag không có → không cần xóa

        # Xóa tag
        new_tags = [t for t in current_tags if t != tag_to_remove]

        # Nếu không còn tag nào hoặc chỉ còn "detected" → xóa toàn bộ record
        if not new_tags or new_tags == ["detected"]:
            logger.info(f"🗑️ Không còn tag vi phạm, xóa record: {track_id}")
            return service.delete_violation(track_id)

        # Update tags mới
        update_payload = {
            "violation_tags": new_tags
        }

        result = service.update_violation(track_id, update_payload)
        if result:
            logger.info(f"✅ Đã xóa tag '{tag_to_remove}' khỏi {track_id}, còn lại: {new_tags}")
        return result is not None

    except Exception as e:
        logger.error(f"❌ Lỗi xóa tag '{tag_to_remove}' của {track_id}: {e}", exc_info=True)
        return False


def upsert_violation_record(violation: Dict[str, Any]) -> Optional[str]:
    """Cập nhật hoặc tạo mới violation theo track_id, giữ toàn bộ lịch sử vi phạm."""
    try:
        track_id = violation.get("track_id")
        if not track_id:
            logger.error("Không có track_id trong violation")
            return None

        service = get_mongodb_service()

        try:
            existing = service.get_violation(track_id)
        except Exception:
            existing = None

        if existing:
            # Lấy violation_tags hiện tại
            tags = existing.get("violation_tags") or []

            # Thêm violation_tags mới từ violation
            new_tags = violation.get("violation_tags", [])
            for tag in new_tags:
                if tag and tag not in tags:
                    tags.append(tag)

            # Sắp xếp theo priority
            tags = _sort_tags(tags)
            dominant_type = tags[0] if tags else "detected"

            history = existing.get("violation_history") or []
            new_entry = _build_history_entry(violation)
            if new_entry.get("type") and new_entry not in history:
                history.append(new_entry)

            update_payload: Dict[str, Any] = {
                "violation_tags": tags,
                "vehicle_type": violation.get("vehicle_type") or existing.get("vehicle_type"),
                "license_plate": violation.get("license_plate") or existing.get("license_plate"),
            }

            if violation.get("timestamp"):
                update_payload["timestamp"] = violation["timestamp"]
            if violation.get("speed") is not None:
                update_payload["speed"] = violation["speed"]
            if violation.get("images"):
                update_payload["images"] = violation["images"]
            if history:
                update_payload["violation_history"] = history

            service.update_violation(track_id, update_payload)
            logger.info(f"Cập nhật violation: track_id={track_id}, type={dominant_type}")
            return track_id

        # Không có record → tạo mới
        # Đảm bảo có violation_tags (đã có trong violation từ creator)
        if "violation_tags" not in violation or not violation["violation_tags"]:
            violation["violation_tags"] = ["detected"]
        if "violation_history" not in violation:
            violation["violation_history"] = [_build_history_entry(violation)]

        created_id = save_violation_to_db(violation)
        if created_id:
            logger.info(f"Tạo mới violation: track_id={track_id}, id={created_id}")
        return created_id

    except Exception as error:
        logger.error(f"Lỗi upsert violation: {error}")
        return None
