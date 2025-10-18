# Tài Liệu: Tính Năng LineB

## Tổng Quan

Thêm tính năng lineB - một đường line song song với stopLine, cách stopLine 64px về phía trên, dùng để xác định vùng giám sát vi phạm giao thông.

## Mô Tả

### StopLine và LineB

```
┌────────────────────────────────────┐
│                                    │
│          (Khu vực trên)            │
│                                    │
├────────────────────────────────────┤ ← LineB (64px phía trên)
│                                    │
│        (Vùng giám sát)             │
│                                    │
├────────────────────────────────────┤ ← StopLine (vạch dừng)
│                                    │
│       (Khu vực sau vạch)           │
│                                    │
└────────────────────────────────────┘
```

### Mục đích

- **StopLine**: Vạch dừng xe thực tế
- **LineB**: Đường song song phía trên, cách 64px, dùng để:
  - Xác định vùng vi phạm (giữa lineB và stopLine)
  - Theo dõi xe tiến gần vạch dừng
  - Tính toán khoảng cách an toàn

## Cách Hoạt Động

### 1. Luồng Xử Lý

```
Frame đầu tiên
     ↓
Detect StopLine (có traffic light check)
     ↓
Tính toán LineB (song song, cách 64px)
     ↓
Trả về cả StopLine và LineB
     ↓
Lưu vào Database (qua API /api/cameras/{id}/regions)
```

### 2. Công Thức Tính LineB

```python
# StopLine: ((x1, y1), (x2, y2)) - normalized [0, 1]
# offset_px = 64 pixels

offset_normalized = 64 / frame_height
lineB_y1 = y1 - offset_normalized
lineB_y2 = y2 - offset_normalized

# LineB: ((x1, lineB_y1), (x2, lineB_y2))
```

**Lưu ý**: LineB có cùng tọa độ x với StopLine (song song), chỉ khác y

## API

### POST `/api/detect/stopline`

Phát hiện stopLine và tự động tính lineB.

**Request:**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

**Response:**
```json
{
  "stopLine": [
    {"x": 0.0, "y": 0.667},
    {"x": 1.0, "y": 0.667}
  ],
  "lineB": [
    {"x": 0.0, "y": 0.578},
    {"x": 1.0, "y": 0.578}
  ]
}
```

### PUT `/api/cameras/{cam_id}/regions`

Lưu stopLine và lineB vào database.

**Request:**
```json
{
  "stopLine": [
    {"x": 0.0, "y": 0.667},
    {"x": 1.0, "y": 0.667}
  ],
  "lineB": [
    {"x": 0.0, "y": 0.578},
    {"x": 1.0, "y": 0.578}
  ],
  "roi": []
}
```

**Response:**
```json
{
  "ok": true
}
```

## Schema Database

### CameraRegion Schema

```python
class CameraRegion(BaseModel):
    stopLine: Optional[tuple[Point, Point]] = None
    lineB: Optional[tuple[Point, Point]] = None
    roi: Optional[list[Point]] = None
```

### Point Schema

```python
class Point(BaseModel):
    x: float  # 0.0 - 1.0
    y: float  # 0.0 - 1.0
```

## Functions

### `calculate_lineB_from_stopline(stopline, frame_height, offset_px=64)`

Tính toán lineB từ stopLine.

**Parameters:**
- `stopline`: Tuple 2 điểm stopLine đã chuẩn hóa
- `frame_height`: Chiều cao frame (pixels)
- `offset_px`: Khoảng cách (pixels), mặc định 64

**Returns:**
- Tuple 2 điểm lineB chuẩn hóa

**Example:**
```python
stopline = ((0.0, 0.667), (1.0, 0.667))
frame_height = 720  # pixels
lineB = calculate_lineB_from_stopline(stopline, frame_height, offset_px=64)
# lineB = ((0.0, 0.578), (1.0, 0.578))
```

## Ví Dụ Sử Dụng

### Ví dụ 1: Frame 720p

```
Frame: 1280x720
StopLine tại y = 480px (normalized: 0.667)
Offset: 64px

LineB tại y = 480 - 64 = 416px
LineB normalized: 416/720 = 0.578
```

### Ví dụ 2: Frame 1080p

```
Frame: 1920x1080
StopLine tại y = 720px (normalized: 0.667)
Offset: 64px

LineB tại y = 720 - 64 = 656px
LineB normalized: 656/1080 = 0.607
```

### Ví dụ 3: StopLine nghiêng

```
StopLine: ((0.1, 0.65), (0.9, 0.68))
Frame height: 720px

LineB: ((0.1, 0.561), (0.9, 0.591))
→ LineB giữ nguyên độ nghiêng, song song với StopLine
```

## Use Cases

### 1. Phát hiện vi phạm vượt đèn đỏ

Xe vượt qua lineB khi đèn đỏ → Cảnh báo tiềm năng vi phạm
Xe vượt qua stopLine khi đèn đỏ → Vi phạm xác nhận

### 2. Tính khoảng cách an toàn

```python
if xe_position.y > lineB.y and xe_position.y < stopLine.y:
    # Xe đang trong vùng cảnh báo
    distance = (stopLine.y - xe_position.y) * frame_height
    print(f"Còn {distance}px tới vạch dừng")
```

### 3. Tracking trajectory

Theo dõi quỹ đạo xe:
- Vào vùng giám sát (qua lineB)
- Dừng đúng vị trí (giữa lineB và stopLine)
- Hoặc vi phạm (vượt stopLine khi đèn đỏ)

## Cấu Hình

### Thay đổi khoảng cách

Mặc định 64px, có thể thay đổi:

```python
# 32px
lineB = calculate_lineB_from_stopline(stopline, frame_height, offset_px=32)

# 96px
lineB = calculate_lineB_from_stopline(stopline, frame_height, offset_px=96)
```

### Tùy chỉnh theo camera

```python
# Camera góc cao: tăng offset
lineB = calculate_lineB_from_stopline(stopline, frame_height, offset_px=80)

# Camera góc thấp: giảm offset
lineB = calculate_lineB_from_stopline(stopline, frame_height, offset_px=48)
```

## Edge Cases

### 1. LineB vượt ra ngoài frame

Nếu stopLine quá gần biên trên (y < 64px):
```python
lineB_y = max(0.0, y - offset_normalized)  # Giới hạn tại y=0
```

### 2. StopLine là đường thẳng đứng

Function vẫn hoạt động bình thường, giữ nguyên x, chỉ dịch chuyển y.

### 3. Frame không phải 16:9

Frame được crop về 16:9 trước khi xử lý, đảm bảo tỷ lệ đúng.

## Logging

```
✓ Phát hiện vạch dừng: [{'x': 0.0, 'y': 0.667}, {'x': 1.0, 'y': 0.667}]
✓ Tính lineB thành công: [{'x': 0.0, 'y': 0.578}, {'x': 1.0, 'y': 0.578}]
```

## Files Liên Quan

- `/backend/schemas/camera.py` - Schema định nghĩa lineB
- `/backend/services/detect_line.py` - Function tính lineB
- `/backend/api/streams.py` - API endpoint detect stopline + lineB
- `/backend/api/cameras.py` - API lưu regions (stopLine + lineB)

## Workflow Tích Hợp

### Frontend Flow

```
1. User upload ảnh hoặc capture frame từ stream
2. POST /api/detect/stopline → Nhận stopLine và lineB
3. User xác nhận hoặc điều chỉnh
4. PUT /api/cameras/{id}/regions → Lưu vào DB
5. Hệ thống sử dụng stopLine + lineB để giám sát vi phạm
```

### Backend Flow

```
1. Nhận frame → Detect stopLine (with traffic light check)
2. Tính lineB từ stopLine (offset 64px)
3. Trả về cả 2 lines
4. Lưu vào MongoDB collection "cameras"
5. Load lại khi cần giám sát stream
```

## Testing

### Test Case 1: Detect và tính lineB

```bash
curl -X POST http://localhost:8000/api/detect/stopline \
  -H "Content-Type: application/json" \
  -d '{"image": "data:image/jpeg;base64,..."}'
```

Expected:
```json
{
  "stopLine": [...],
  "lineB": [...]
}
```

### Test Case 2: Lưu vào DB

```bash
curl -X PUT http://localhost:8000/api/cameras/cam1/regions \
  -H "Content-Type: application/json" \
  -d '{
    "stopLine": [[{"x": 0.0, "y": 0.667}, {"x": 1.0, "y": 0.667}]],
    "lineB": [[{"x": 0.0, "y": 0.578}, {"x": 1.0, "y": 0.578}]]
  }'
```

## Changelog

### v1.2.0 - Thêm LineB Feature
- Thêm field `lineB` vào `CameraRegion` schema
- Thêm function `calculate_lineB_from_stopline()` 
- Cập nhật API `/api/detect/stopline` trả về cả stopLine và lineB
- Tự động tính lineB song song với stopLine, cách 64px
- Support lưu lineB vào database qua API `/api/cameras/{id}/regions`
