"""
Hằng số cố định - Không thể config

Chỉ chứa các giá trị cố định như màu sắc
Các tham số khác đã chuyển sang .env
"""

from typing import Dict, Tuple

# Màu sắc cho từng class (BGR format cho OpenCV)
COLORS_BY_CLASS: Dict[str, Tuple[int, int, int]] = {
    "bus": (0, 255, 255),           # Vàng
    "car": (255, 0, 0),              # Xanh dương
    "helmet": (0, 255, 0),           # Xanh lá
    "license_plate": (255, 255, 0),  # Cyan
    "light_green": (0, 255, 0),      # Xanh lá
    "light_red": (0, 0, 255),        # Đỏ
    "light_yellow": (0, 255, 255),   # Vàng
    "motorcycle": (255, 0, 255),     # Magenta
    "no_helmet": (0, 0, 255),        # Đỏ
    "truck": (128, 0, 128),          # Tím
}

# Màu mặc định
DEFAULT_COLOR: Tuple[int, int, int] = (255, 255, 255)  # Trắng
