# Tạo ROI Tự Động Từ LineB

## Tính năng mới

### ✅ ROI tự động được tạo từ lineB
- **Cạnh trên:** LineB (kéo dài đến x=0 và x=1)
- **Cạnh dưới:** Đáy stream (y=1)
- **Tự động lưu vào DB** cùng với stopLine và lineB

## Workflow

```
StopLine → LineB → ROI
         ↓        ↓     ↓
     Detect   +64px  lineB→bottom
```

### Thứ tự xử lý:
1. **Detect stopLine** (Canny + Hough hoặc mặc định 2/3)
2. **Tính lineB** từ stopLine (offset 64px lên trên)
3. **Tạo ROI** từ lineB (từ lineB xuống đáy, kéo dài hết chiều ngang)

## Visual Result

```
┌─────────────────────────────────────┐
│         (Camera view)               │
│                                     │
├─────────────────────────────────────┤ ← LineB (y_top)
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ ← ROI (vùng giám sát)
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
├─────────────────────────────────────┤ ← StopLine
│                                     │
└─────────────────────────────────────┘ ← Đáy (y=1)
```

### ROI Points (4 điểm):
```javascript
[
  {x: 0.0, y: y_lineB},    // Top-left
  {x: 1.0, y: y_lineB},    // Top-right
  {x: 1.0, y: 1.0},        // Bottom-right
  {x: 0.0, y: 1.0},        // Bottom-left
]
```

## Files Changed

### 1. Backend: `services/detect_line.py`

**Function mới:**
```python
def calculate_roi_from_lineB(
    lineB_result: Tuple[Tuple[float, float], Tuple[float, float]]
) -> List[Tuple[float, float]]:
    """
    Tạo ROI tự động từ lineB
    ROI là hình chữ nhật với:
    - Cạnh trên: lineB kéo dài đến 2 bên (x=0 và x=1)
    - Cạnh dưới: đáy stream (y=1)
    """
    (x1, y1), (x2, y2) = lineB_result
    y_top = (y1 + y2) / 2.0
    
    roi_points = [
        (0.0, y_top),   # Top-left
        (1.0, y_top),   # Top-right
        (1.0, 1.0),     # Bottom-right
        (0.0, 1.0),     # Bottom-left
    ]
    
    return roi_points
```

### 2. Backend: `api/streams.py`

**API Response mới:**
```json
{
  "stopLine": [
    {"x": 0.0, "y": 0.667},
    {"x": 1.0, "y": 0.667}
  ],
  "lineB": [
    {"x": 0.0, "y": 0.548},
    {"x": 1.0, "y": 0.548}
  ],
  "roi": [
    {"x": 0.0, "y": 0.548},
    {"x": 1.0, "y": 0.548},
    {"x": 1.0, "y": 1.0},
    {"x": 0.0, "y": 1.0}
  ]
}
```

### 3. Frontend: `RegionEditorModal.tsx`

**Cập nhật:**
```tsx
const roi = data?.roi
if (roi && roi.length >= 3) {
  payload.roi = roi
}

message.success(`Đã phát hiện và lưu: ${parts.join(' + ')}`)
// → "Đã phát hiện và lưu: stopLine + lineB + ROI"
```

### 4. Frontend: `CameraTile.tsx`

**Auto detect khi stream load:**
```tsx
const roi = data?.roi
if (roi && roi.length >= 3) {
  payload.roi = roi
}
// Tự động lưu cả 3: stopLine, lineB, ROI
```

## Test Cases

### Test 1: Manual detect (Click "Line tự động")

**Steps:**
1. Mở camera tile
2. Click "Thiết lập vùng"
3. Click "Line tự động"

**Expected:**
- ✅ Message: "Đã phát hiện và lưu: stopLine + lineB + ROI"
- ✅ UI hiển thị:
  - StopLine (đỏ)
  - LineB (đỏ)
  - ROI (polygon xanh lá, bao từ lineB xuống đáy)
- ✅ Database có cả 3 fields

### Test 2: Auto detect (Stream mới load)

**Steps:**
1. Thêm camera mới với RTSP
2. Save
3. Đợi stream load

**Expected:**
- ✅ Tự động detect và lưu cả 3
- ✅ UI hiển thị ngay stopLine + lineB + ROI
- ✅ Không cần click nút nào

### Test 3: Backend logs

**Check logs:**
```bash
docker compose logs backend --tail 50
```

**Expected:**
```
✓ Phát hiện vạch dừng: [...]
✓ Tính lineB thành công: [...]
✓ Tính ROI thành công: 4 điểm
📦 Payload nhận được: {'stopLine': [...], 'lineB': [...], 'roi': [...]}
```

### Test 4: Database

```javascript
db.cameras.findOne({id: "cam-01"})
```

**Expected:**
```javascript
{
  regions: {
    stopLine: [
      {x: 0.0, y: 0.667},
      {x: 1.0, y: 0.667}
    ],
    lineB: [
      {x: 0.0, y: 0.548},
      {x: 1.0, y: 0.548}
    ],
    roi: [                      // ✅ ROI tự động
      {x: 0.0, y: 0.548},
      {x: 1.0, y: 0.548},
      {x: 1.0, y: 1.0},
      {x: 0.0, y: 1.0}
    ]
  }
}
```

## Logic

### Tính toán ROI

```python
# Input: lineB = [(x1, y1), (x2, y2)]
# Với lineB có thể nghiêng một chút

# Bước 1: Lấy y trung bình
y_top = (y1 + y2) / 2.0

# Bước 2: Tạo 4 điểm ROI
roi = [
  (0.0, y_top),     # Góc trên trái
  (1.0, y_top),     # Góc trên phải
  (1.0, 1.0),       # Góc dưới phải (đáy)
  (0.0, 1.0),       # Góc dưới trái (đáy)
]
```

### Ví dụ:

**Input:**
```
lineB = [(0.0, 0.55), (1.0, 0.57)]  // Nghiêng nhẹ
```

**Calculation:**
```
y_top = (0.55 + 0.57) / 2 = 0.56
```

**Output:**
```
roi = [
  (0.0, 0.56),   // Top-left
  (1.0, 0.56),   // Top-right
  (1.0, 1.0),    // Bottom-right
  (0.0, 1.0),    // Bottom-left
]
```

## Cấu hình

### Điều chỉnh offset lineB (ảnh hưởng đến ROI)

Edit `.env`:
```bash
LINE_B_OFFSET_PX=80   # Tăng offset → ROI cao hơn
LINE_B_OFFSET_PX=50   # Giảm offset → ROI thấp hơn
```

Restart backend:
```bash
docker compose restart backend
```

### Tại sao ROI từ lineB?

- **Vùng giám sát** nằm **giữa lineB và stopLine**
- Các phương tiện vượt qua lineB sẽ được theo dõi
- ROI giúp filter chỉ detect trong vùng quan tâm
- Giảm false positive từ các xe ngoài vùng

## Troubleshooting

### ROI không hiển thị

**Check 1: Response từ backend**
```javascript
// Console (F12)
🎯 Response data: {stopLine: [...], lineB: [...], roi: [...]}
```

Nếu không có `roi` → Backend có lỗi

**Check 2: Backend logs**
```bash
docker compose logs backend --tail 30 | grep ROI
```

Expected: `✓ Tính ROI thành công: 4 điểm`

**Check 3: Database**
```javascript
db.cameras.findOne({id: "cam-01"}, {regions: 1})
```

Nếu không có `regions.roi` → Không lưu được

### ROI hiển thị sai

**Check coordinates:**
```javascript
// ROI phải có 4 điểm
roi.length === 4

// Y của 2 điểm trên phải bằng nhau (cạnh trên ngang)
roi[0].y === roi[1].y

// Y của 2 điểm dưới phải là 1.0 (đáy)
roi[2].y === 1.0 && roi[3].y === 1.0
```

### ROI quá cao hoặc quá thấp

→ Điều chỉnh `LINE_B_OFFSET_PX` trong `.env`

## Summary

### ✅ Tính năng mới
- ROI tự động từ lineB
- Tự động detect khi stream load
- Tự động lưu vào DB

### 📊 Workflow
```
Camera stream load
       ↓
Detect stopLine
       ↓
Tính lineB (+64px)
       ↓
Tạo ROI (lineB → đáy)
       ↓
Lưu cả 3 vào DB
       ↓
UI hiển thị cả 3
```

### 🎯 Kết quả
- Không cần vẽ ROI thủ công
- ROI luôn chính xác với vùng giám sát
- Tiết kiệm thời gian setup camera

---

**ROI tự động hoàn tất!** 🎉
