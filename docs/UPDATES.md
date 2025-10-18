# Bản Cập Nhật Tính Năng

## Ngày: 17/10/2025

### Tóm Tắt

Đã thêm 2 tính năng chính cho hệ thống phát hiện vạch dừng:

1. **Traffic Light Check** - Kiểm tra đèn giao thông trước khi detect line
2. **LineB Feature** - Thêm line song song với stopLine, cách 64px

---

## 📋 Chi Tiết Thay Đổi

### 1. Traffic Light Detection Logic

#### Mô tả
Trước khi detect stopLine, hệ thống kiểm tra xem frame có đèn giao thông không:
- **Có traffic light** → Sử dụng detect line tự động (Canny + HoughLinesP)
- **Không có traffic light** → Tạo line ngang mặc định ở vị trí 2/3 chiều cao

#### Files thay đổi
- `backend/services/detect_line.py`
  - Thêm `_has_traffic_lights()` - Kiểm tra traffic light
  - Thêm `_create_default_stopline()` - Tạo line mặc định
  - Thêm `detect_stop_line_with_fallback()` - Logic chính

- `backend/api/streams.py`
  - Cập nhật endpoint `/api/detect/stopline` sử dụng logic mới

#### Tài liệu
📖 Chi tiết: `/docs/STOPLINE_DETECTION.md`

---

### 2. LineB Feature

#### Mô tả
Thêm lineB - đường line song song với stopLine, cách stopLine 64px về phía trên:

```
├────────────────────────────────────┤ ← LineB (64px phía trên)
│        (Vùng giám sát)             │
├────────────────────────────────────┤ ← StopLine
```

#### Công thức
```python
offset_normalized = 64 / frame_height
lineB_y = stopLine_y - offset_normalized
```

#### Files thay đổi

**Schema:**
- `backend/schemas/camera.py`
  - Thêm field `lineB` vào `CameraRegion`

**Service:**
- `backend/services/detect_line.py`
  - Thêm `calculate_lineB_from_stopline()` - Tính lineB từ stopLine

**API:**
- `backend/api/streams.py`
  - Cập nhật endpoint `/api/detect/stopline` trả về cả stopLine và lineB

**Database:**
- `backend/api/cameras.py` - Tự động hỗ trợ lưu lineB (qua schema)

#### Response API

**Trước:**
```json
{
  "stopLine": [
    {"x": 0.0, "y": 0.667},
    {"x": 1.0, "y": 0.667}
  ]
}
```

**Sau:**
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

#### Tài liệu
📖 Chi tiết: `/docs/LINEB_FEATURE.md`

---

## 🚀 Cách Sử Dụng

### Detect StopLine và LineB

```bash
curl -X POST http://localhost:8000/api/detect/stopline \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/jpeg;base64,..."
  }'
```

**Response:**
```json
{
  "stopLine": [[{"x": 0.0, "y": 0.667}, {"x": 1.0, "y": 0.667}]],
  "lineB": [[{"x": 0.0, "y": 0.578}, {"x": 1.0, "y": 0.578}]]
}
```

### Lưu vào Database

```bash
curl -X PUT http://localhost:8000/api/cameras/cam1/regions \
  -H "Content-Type: application/json" \
  -d '{
    "stopLine": [[{"x": 0.0, "y": 0.667}, {"x": 1.0, "y": 0.667}]],
    "lineB": [[{"x": 0.0, "y": 0.578}, {"x": 1.0, "y": 0.578}]]
  }'
```

---

## 🔧 Testing

### Test Traffic Light Check

**Test Case 1: Frame có traffic light**
```python
# Expect: Detect line tự động
# Log: "✓ Phát hiện đèn giao thông: light_red"
```

**Test Case 2: Frame không có traffic light**
```python
# Expect: Line mặc định tại y=0.667
# Log: "✗ Không phát hiện đèn giao thông"
```

### Test LineB Calculation

**Test Case 1: Frame 720p**
```python
stopline = ((0.0, 0.667), (1.0, 0.667))
lineB = calculate_lineB_from_stopline(stopline, 720, 64)
# Expected: ((0.0, 0.578), (1.0, 0.578))
```

**Test Case 2: StopLine nghiêng**
```python
stopline = ((0.1, 0.65), (0.9, 0.68))
lineB = calculate_lineB_from_stopline(stopline, 720, 64)
# Expected: LineB song song, giữ độ nghiêng
```

---

## 📊 Database Schema

### CameraRegion (Updated)

```python
{
  "stopLine": [
    {"x": 0.0, "y": 0.667},
    {"x": 1.0, "y": 0.667}
  ],
  "lineB": [              # ← NEW
    {"x": 0.0, "y": 0.578},
    {"x": 1.0, "y": 0.578}
  ],
  "roi": []
}
```

---

## 🎯 Use Cases

### 1. Phát hiện vi phạm vượt đèn đỏ
- Xe qua lineB khi đèn đỏ → Cảnh báo
- Xe qua stopLine khi đèn đỏ → Vi phạm xác nhận

### 2. Tính khoảng cách an toàn
```python
if vehicle.y > lineB.y and vehicle.y < stopLine.y:
    distance = (stopLine.y - vehicle.y) * frame_height
    print(f"Cảnh báo: Còn {distance}px tới vạch dừng")
```

### 3. Tracking trajectory
- Theo dõi xe từ lineB → stopLine
- Phát hiện hành vi vi phạm

---

## 📝 Logging

Hệ thống ghi log chi tiết:

```
✓ Phát hiện đèn giao thông: light_red
Sử dụng detect line tự động (có traffic light)
✓ Detect line thành công: ((0.0, 0.667), (1.0, 0.667))
✓ Tính lineB thành công: [{'x': 0.0, 'y': 0.578}, {'x': 1.0, 'y': 0.578}]
```

---

## 🔄 Workflow Integration

```
User Upload Frame
       ↓
Check Traffic Light
       ↓
   ┌───┴───┐
   ↓       ↓
  Có    Không
   ↓       ↓
Auto    Default
Detect   Line
   ↓       ↓
   └───┬───┘
       ↓
  Detect StopLine
       ↓
Calculate LineB (64px offset)
       ↓
Return {stopLine, lineB}
       ↓
Save to Database
```

---

## 🐛 Known Issues & Edge Cases

### 1. LineB vượt frame
✅ **Resolved**: Giới hạn tại y=0
```python
lineB_y = max(0.0, y - offset_normalized)
```

### 2. Frame không phải 16:9
✅ **Resolved**: Auto crop về 16:9 trước khi xử lý

### 3. Traffic light detection thất bại
✅ **Fallback**: Tạo line mặc định

---

## 📦 Dependencies

Không có dependency mới, sử dụng các thư viện có sẵn:
- `cv2` (OpenCV)
- `numpy`
- `ultralytics` (YOLO)
- `pymongo` (MongoDB)

---

## ⚙️ Configuration

### Thay đổi khoảng cách lineB

Trong `api/streams.py` line 169:
```python
# Mặc định 64px
lineB_result = calculate_lineB_from_stopline(stopline_result, h, offset_px=64)

# Tùy chỉnh
lineB_result = calculate_lineB_from_stopline(stopline_result, h, offset_px=80)
```

### Traffic light classes

Trong `services/detect_line.py` line 250:
```python
traffic_light_classes = {"light_red", "light_green", "light_yellow"}
```

---

## 📚 Tài Liệu Liên Quan

- `/docs/STOPLINE_DETECTION.md` - Chi tiết traffic light check
- `/docs/LINEB_FEATURE.md` - Chi tiết lineB feature
- `/backend/schemas/camera.py` - Schema definitions
- `/backend/services/detect_line.py` - Core logic
- `/backend/api/streams.py` - API endpoints

---

## ✅ Checklist

- [x] Thêm traffic light detection logic
- [x] Thêm function `calculate_lineB_from_stopline()`
- [x] Cập nhật schema thêm field `lineB`
- [x] Cập nhật API endpoint trả về lineB
- [x] Support lưu lineB vào database
- [x] Tạo tài liệu đầy đủ
- [x] Test các edge cases
- [x] Logging đầy đủ

---

## 🔮 Future Enhancements

1. **Dynamic offset**: Tự động tính offset dựa trên góc camera
2. **Multiple lines**: Support nhiều lines (A, B, C, ...) 
3. **Line validation**: Kiểm tra lineB có hợp lệ không
4. **Visual debug**: Vẽ lineB lên stream để debug
5. **Analytics**: Thống kê số xe trong vùng lineB-stopLine

---

## 👥 Authors

- **Feature**: Traffic Light Check + LineB
- **Date**: 17/10/2025
- **Version**: 1.2.0
