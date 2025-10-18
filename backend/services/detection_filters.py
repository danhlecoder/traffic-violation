"""
Detection Filters - Lọc detections theo ROI và logic nghiệp vụ
"""

from typing import List, Dict, Any, Optional
import cv2
import numpy as np


def is_bbox_in_roi(bbox: List[float], roi: List[Dict[str, float]], img_width: int, img_height: int) -> bool:
    """
    Kiểm tra bbox có nằm trong ROI không
    
    Args:
        bbox: [x1, y1, x2, y2] tọa độ pixel
        roi: List các điểm ROI normalized [{x, y}, ...]
        img_width: Chiều rộng ảnh
        img_height: Chiều cao ảnh
    
    Returns:
        True nếu center bbox nằm trong ROI
    """
    if not roi or len(roi) < 3:
        return True
    
    # Tính center của bbox
    x1, y1, x2, y2 = bbox
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    
    # Chuyển ROI từ normalized về pixel
    roi_pixels = np.array([[p['x'] * img_width, p['y'] * img_height] for p in roi], dtype=np.int32)
    
    # Kiểm tra point in polygon
    result = cv2.pointPolygonTest(roi_pixels, (center_x, center_y), False)
    return result >= 0


def is_bbox_inside_bbox(inner_bbox: List[float], outer_bbox: List[float]) -> bool:
    """
    Kiểm tra bbox con có nằm trong bbox cha không
    
    Args:
        inner_bbox: [x1, y1, x2, y2] của bbox con
        outer_bbox: [x1, y1, x2, y2] của bbox cha
    
    Returns:
        True nếu center của inner nằm trong outer
    """
    inner_cx = (inner_bbox[0] + inner_bbox[2]) / 2
    inner_cy = (inner_bbox[1] + inner_bbox[3]) / 2
    
    outer_x1, outer_y1, outer_x2, outer_y2 = outer_bbox
    
    return (outer_x1 <= inner_cx <= outer_x2 and
            outer_y1 <= inner_cy <= outer_y2)


def filter_detections_by_roi(
    detections: List[Dict[str, Any]],
    roi: Optional[List[Dict[str, float]]],
    img_width: int,
    img_height: int
) -> List[Dict[str, Any]]:
    """
    Filter detections theo ROI với logic đặc biệt:
    
    1. Đèn giao thông (light_*): Luôn hiển thị (cả ngoài ROI)
    2. Biển số (license_plate): Chỉ hiện khi nằm trong bbox xe
    3. Mũ bảo hiểm (helmet, no_helmet): Chỉ hiện khi nằm trong bbox xe máy
    4. Phương tiện khác: Filter theo ROI
    
    Args:
        detections: List detections từ YOLO
        roi: ROI normalized [{x, y}, ...] hoặc None
        img_width: Chiều rộng ảnh
        img_height: Chiều cao ảnh
    
    Returns:
        List detections đã filter
    """
    if not detections:
        return []
    
    TRAFFIC_LIGHTS = {"light_green", "light_red", "light_yellow"}
    VEHICLES = {"bus", "car", "motorcycle", "truck"}
    
    # Tách detections theo loại
    lights = []
    vehicles = []
    plates = []
    helmets = []
    others = []
    
    for det in detections:
        class_name = det["class_name"]
        if class_name in TRAFFIC_LIGHTS:
            lights.append(det)
        elif class_name in VEHICLES:
            vehicles.append(det)
        elif class_name == "license_plate":
            plates.append(det)
        elif class_name in {"helmet", "no_helmet"}:
            helmets.append(det)
        else:
            others.append(det)
    
    filtered = []
    
    # 1. Đèn giao thông: Luôn hiển thị
    filtered.extend(lights)
    
    # 2. Vehicles: Filter theo ROI (nếu có)
    if roi and len(roi) >= 3:
        vehicles_in_roi = []
        for det in vehicles:
            if is_bbox_in_roi(det["bbox"], roi, img_width, img_height):
                vehicles_in_roi.append(det)
        filtered.extend(vehicles_in_roi)
    else:
        filtered.extend(vehicles)
    
    # 3. Biển số: Chỉ hiện khi nằm trong bbox xe
    vehicles_in_filtered = [v for v in vehicles if v in filtered]
    for plate in plates:
        for vehicle in vehicles_in_filtered:
            if is_bbox_inside_bbox(plate["bbox"], vehicle["bbox"]):
                filtered.append(plate)
                break
    
    # 4. Mũ bảo hiểm: Chỉ hiện khi nằm trong bbox xe máy
    motorcycles_in_filtered = [v for v in vehicles_in_filtered if v["class_name"] == "motorcycle"]
    for helmet in helmets:
        for motorcycle in motorcycles_in_filtered:
            if is_bbox_inside_bbox(helmet["bbox"], motorcycle["bbox"]):
                filtered.append(helmet)
                break
    
    # 5. Others: Filter theo ROI (nếu có)
    if roi and len(roi) >= 3:
        for det in others:
            if is_bbox_in_roi(det["bbox"], roi, img_width, img_height):
                filtered.append(det)
    else:
        filtered.extend(others)
    
    return filtered
