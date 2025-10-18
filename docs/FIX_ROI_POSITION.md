# Fix: ROI Đúng Vị Trí + Nút "ROI Tự Động"

## Vấn đề ban đầu

Trong ảnh có thấy:
- ✅ LineB (đỏ) ở vị trí cao
- ❌ ROI (xanh lá) ở giữa lineB và stopLine
- ❌ ROI SAI - phải từ lineB xuống đáy, không phải ở giữa!

## Root Cause

1. **ROI cũ** được vẽ bằng tay (mode draw-roi) → Vị trí sai
2. **Không có nút "ROI tự động"** → User không thể tạo ROI đúng từ lineB
3. **Logic vẽ bằng bút** → Cho phép vẽ ROI tùy ý (có thể sai vị trí)

## Đã Fix

### 1. ✅ Thêm nút "ROI tự động"

**File:** `frontend/src/components/RegionEditorModal.tsx`

**Function mới:**
```tsx
const createAutoROI = useCallback(async () => {
  const lineB = cameraRegion.lineB
  if (!lineB || lineB.length !== 2) {
    message.error('Cần có lineB trước. Click "Line tự động" để tạo.')
    return
  }

  // Tính y trung bình của lineB làm cạnh trên
  const y_top = (lineB[0].y + lineB[1].y) / 2

  // Tạo 4 điểm ROI: từ lineB xuống đáy, kéo dài hết chiều ngang
  const roi = [
    { x: 0, y: y_top },   // Top-left
    { x: 1, y: y_top },   // Top-right
    { x: 1, y: 1 },       // Bottom-right
    { x: 0, y: 1 },       // Bottom-left
  ]

  setCameraRegion(cameraId, { roi })
  await streams.updateCameraRegions(cameraId, { roi })
  message.success('Đã tạo ROI tự động từ lineB')
}, [cameraRegion.lineB, cameraId, setCameraRegion])
```

**Nút trong toolbar:**
```tsx
{cameraRegion.lineB && (
  <Tooltip title="Tạo ROI từ lineB hiện tại">
    <Button size="small" onClick={createAutoROI}>ROI tự động</Button>
  </Tooltip>
)}
```

### 2. ✅ Xóa ROI khi xóa line

**TRƯỚC:**
```tsx
// Chỉ xóa stopLine và lineB
onClick={async () => {
  clearCameraRegion(cameraId, 'stopLine')
  clearCameraRegion(cameraId, 'lineB')
  try { await streams.updateCameraRegions(cameraId, { stopLine: null, lineB: null }) } catch {}
}}
```

**SAU:**
```tsx
// Xóa cả ROI
onClick={async () => {
  clearCameraRegion(cameraId, 'stopLine')
  clearCameraRegion(cameraId, 'lineB')
  clearCameraRegion(cameraId, 'roi')  // ✅ Thêm
  try { await streams.updateCameraRegions(cameraId, { stopLine: null, lineB: null, roi: null }) } catch {}
}}
```

### 3. ✅ Backend đã trả về ROI

**API Response:**
```json
{
  "stopLine": [...],
  "lineB": [...],
  "roi": [              // ✅ Auto từ lineB
    {"x": 0.0, "y": 0.548},
    {"x": 1.0, "y": 0.548},
    {"x": 1.0, "y": 1.0},
    {"x": 0.0, "y": 1.0}
  ]
}
```

## Workflow Mới

### Cách 1: Tự động toàn bộ (Khuyến nghị)

```
1. Click "Line tự động"
   ↓
2. Detect: stopLine → lineB → ROI
   ↓
3. Lưu cả 3 vào DB
   ↓
4. UI hiển thị đúng
```

### Cách 2: Tạo ROI riêng (Nếu đã có lineB)

```
1. Đã có lineB (từ "Line tự động" trước đó)
   ↓
2. Click "ROI tự động"
   ↓
3. Tạo ROI từ lineB hiện tại
   ↓
4. Lưu vào DB
```

### Cách 3: Vẽ bằng bút (Manual)

```
1. Click nút "ROI"
   ↓
2. Click ≥3 điểm để vẽ polygon
   ↓
3. Enter để lưu
   ↓
⚠️ CẢNH BÁO: ROI có thể sai vị trí nếu vẽ tay!
   → Nên dùng "ROI tự động" thay vì vẽ tay
```

## Test Cases

### Test 1: Xóa ROI cũ (sai vị trí)

**Steps:**
1. Mở camera có ROI cũ (vẽ tay)
2. Click "Xóa ROI"
3. Verify: ROI biến mất

### Test 2: Tạo ROI đúng vị trí

**Steps:**
1. Click "Line tự động"
   → Message: "Đã phát hiện và lưu: stopLine + lineB + ROI"
2. Kiểm tra UI:
   - LineB (đỏ) ở trên
   - ROI (xanh lá) từ lineB xuống đáy
   - StopLine (đỏ) ở dưới

**Expected:**
```
┌─────────────────────┐
│                     │
├─────────────────────┤ ← LineB (đỏ)
│ ░░░░░░░░░░░░░░░░░░ │
│ ░░░░ ROI ░░░░░░░░░ │ ← Từ lineB xuống đáy
│ ░░░░░░░░░░░░░░░░░░ │
├─────────────────────┤ ← StopLine (đỏ)
│                     │
└─────────────────────┘
```

### Test 3: Nút "ROI tự động"

**Steps:**
1. Đảm bảo đã có lineB
2. Click "ROI tự động"
   → Message: "Đã tạo ROI tự động từ lineB"
3. Kiểm tra: ROI từ lineB xuống đáy ✅

### Test 4: Không có lineB

**Steps:**
1. Chưa có lineB
2. Click "ROI tự động" (nút không hiển thị)

**Expected:**
- Nút "ROI tự động" chỉ hiện khi có lineB

### Test 5: Xóa line → ROI cũng xóa

**Steps:**
1. Có stopLine + lineB + ROI
2. Click "Xóa line"
3. Verify: Cả 3 đều biến mất ✅

## Database Check

```javascript
// Kiểm tra ROI đúng format
db.cameras.findOne({id: "cam-01"})

// Expected:
{
  regions: {
    stopLine: [...],
    lineB: [...],
    roi: [
      {x: 0.0, y: 0.548},  // Top-left: x=0, y=lineB
      {x: 1.0, y: 0.548},  // Top-right: x=1, y=lineB
      {x: 1.0, y: 1.0},    // Bottom-right: x=1, y=1 (đáy)
      {x: 0.0, y: 1.0}     // Bottom-left: x=0, y=1 (đáy)
    ]
  }
}
```

**Validate ROI:**
```javascript
const roi = regions.roi

// Check 1: Có 4 điểm
roi.length === 4 // ✅

// Check 2: Cạnh trên ngang (y giống nhau)
roi[0].y === roi[1].y // ✅

// Check 3: Cạnh dưới là đáy (y=1)
roi[2].y === 1.0 && roi[3].y === 1.0 // ✅

// Check 4: Kéo dài hết chiều ngang
roi[0].x === 0.0 && roi[1].x === 1.0 // ✅
```

## Hướng Dẫn Sử Dụng

### Khuyến nghị: Dùng "Line tự động"

```
1. Mở camera tile
2. Click "Thiết lập vùng"
3. Click "Line tự động"
4. Xong! ✅
   → Có: stopLine + lineB + ROI (đúng vị trí)
```

### Nếu muốn tạo lại ROI

```
1. Click "Xóa ROI" (xóa ROI cũ)
2. Click "ROI tự động"
   → ROI mới từ lineB xuống đáy ✅
```

### Nếu ROI đang sai vị trí

```
Nguyên nhân: ROI cũ vẽ bằng tay

Giải pháp:
1. Click "Xóa ROI"
2. Click "ROI tự động"
3. Hoặc click "Line tự động" (tạo lại cả 3)
```

## Tóm Tắt Thay Đổi

### ✅ Thêm mới
- Nút "ROI tự động" trong RegionEditorModal
- Function `createAutoROI()` tạo ROI từ lineB

### ✅ Cập nhật
- Nút "Xóa line" giờ xóa cả ROI
- Tooltip "Line tự động" giờ ghi rõ "stopLine + lineB + ROI"

### 📝 Backend (đã có từ trước)
- API `/detect/stopline` trả về ROI
- Function `calculate_roi_from_lineB()` trong `detect_line.py`

### 🎯 Kết quả
- ROI luôn đúng vị trí (từ lineB xuống đáy)
- User có 2 cách: "Line tự động" hoặc "ROI tự động"
- Không khuyến khích vẽ ROI bằng tay nữa

## Troubleshooting

### ROI vẫn sai vị trí sau khi click "Line tự động"

**Check 1: Clear cache**
```
Ctrl + Shift + R
```

**Check 2: Database có ROI cũ?**
```javascript
db.cameras.findOne({id: "cam-01"})
// Nếu roi có vị trí sai → Xóa và tạo lại
```

**Fix:**
```
1. Click "Xóa line" (xóa cả 3)
2. Click "Line tự động" lại
```

### Nút "ROI tự động" không hiển thị

**Nguyên nhân:** Chưa có lineB

**Fix:**
```
Click "Line tự động" trước
→ Sẽ tạo cả stopLine + lineB + ROI
```

### ROI không hiển thị UI

**Check:** Console (F12)
```javascript
// Kiểm tra data
cameraRegion.roi
// Expected: [{x, y}, {x, y}, {x, y}, {x, y}]
```

**Fix:**
```
docker compose logs frontend --tail 50
```

## Summary

### 🎯 Vấn đề đã fix
- ROI cũ ở vị trí sai (giữa lineB và stopLine)
- Không có cách tạo ROI đúng ngoài vẽ tay

### ✅ Giải pháp
- Thêm nút "ROI tự động"
- Xóa ROI khi xóa line
- Tạo ROI đúng từ lineB (cạnh trên = lineB, cạnh dưới = đáy)

### 📖 Workflow
```
Line tự động → stopLine + lineB + ROI (auto)
            hoặc
ROI tự động → ROI từ lineB hiện tại
```

---

**ROI giờ luôn đúng vị trí!** 🎉
