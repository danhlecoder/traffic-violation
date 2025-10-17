# Service Đếm Mật Độ Phương Tiện

## Tổng quan
Service `dem_phuong_tien.py` cung cấp các hàm để đếm và phân loại mật độ phương tiện dựa trên kết quả detection từ YOLO.

## Các loại phương tiện được đếm
- `bus`: Xe buýt
- `car`: Ô tô
- `motorcycle`: Xe máy
- `truck`: Xe tải

## Phân loại mật độ

| Số lượng xe | Mức độ | Mô tả |
|-------------|--------|-------|
| 0           | empty  | Vắng  |
| 1-5         | low    | Thưa  |
| 6-15        | medium | Đông  |
| >15         | high   | Rất đông |

## Các hàm chính

### 1. `count_vehicles(detections)`
Đếm tổng số phương tiện trong danh sách detections.

**Input:**
```python
detections = [
    {
        "bbox": [x1, y1, x2, y2],
        "confidence": 0.85,
        "class_id": 2,
        "class_name": "car"
    },
    ...
]
```

**Output:**
```python
vehicle_count = 5  # int
```

### 2. `get_vehicle_density_info(vehicle_count)`
Lấy thông tin chi tiết về mật độ.

**Input:**
```python
vehicle_count = 10
```

**Output:**
```python
{
    "count": 10,
    "level": "medium",
    "description": "Đông"
}
```

### 3. `get_vehicles_by_type(detections)`
Đếm số lượng từng loại phương tiện.

**Input:**
```python
detections = [...]  # Danh sách detections
```

**Output:**
```python
{
    "car": 5,
    "motorcycle": 3,
    "bus": 1,
    "truck": 0
}
```

## Sử dụng trong code

### Trong streaming service:
```python
from .dem_phuong_tien import count_vehicles, get_vehicle_density_info

# Sau khi detect
detections = detector.detect(frame)

# Đếm phương tiện
vehicle_count = count_vehicles(detections)

# Lấy thông tin mật độ
density_info = get_vehicle_density_info(vehicle_count)
print(f"Phát hiện {vehicle_count} xe - {density_info['description']}")
```

### Qua API:
```bash
# Lấy thông tin mật độ cho 10 xe
GET /api/density/info?vehicle_count=10

# Response:
{
    "count": 10,
    "level": "medium",
    "description": "Đông"
}
```

## Cấu hình ngưỡng

Các ngưỡng phân loại được định nghĩa trong `backend/core/constants.py`:

```python
DENSITY_THRESHOLD_LOW = 5      # <= 5 xe: Thưa
DENSITY_THRESHOLD_MEDIUM = 15  # <= 15 xe: Đông
```

Có thể điều chỉnh các giá trị này để phù hợp với yêu cầu cụ thể.
