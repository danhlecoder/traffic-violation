# Fix: Auto Detect Không Lưu LineB

## Vấn đề đã tìm ra

Có **2 luồng** detect stopLine:

### 1. ✅ Thủ công (Click "Line tự động" trong modal)
**File:** `RegionEditorModal.tsx`
```typescript
const lineB = data?.lineB
if (lineB && lineB.length === 2) {
  payload.lineB = lineB  // ✅ ĐÃ xử lý lineB
}
```
→ **Có lineB**

### 2. ❌ Tự động (Khi thêm camera mới, stream load lên)
**File:** `CameraTile.tsx`
```typescript
const line = data?.stopLine
const payload = { stopLine: line }  // ❌ THIẾU lineB!
```
→ **Không có lineB**

## Đã fix

**File:** `frontend/src/components/CameraTile.tsx`

**TRƯỚC:**
```typescript
const data = await resp.json()
const line = data?.stopLine
if (line && line.length === 2) {
  const payload = { stopLine: line as any }  // ❌ CHỈ có stopLine
  setCameraRegion(cameraId, payload)
  // ...
}
```

**SAU:**
```typescript
const data = await resp.json()
const line = data?.stopLine
const lineB = data?.lineB                    // ✅ Lấy lineB
if (line && line.length === 2) {
  const payload: any = { stopLine: line }
  if (lineB && lineB.length === 2) {
    payload.lineB = lineB                    // ✅ Thêm lineB vào payload
  }
  setCameraRegion(cameraId, payload)
  // ...
}
```

## Test Case

### Test 1: Thêm camera mới (Auto detect)

**Steps:**
1. Thêm camera mới với RTSP
2. Đợi stream load lên
3. Hệ thống tự động detect stopLine

**Expected:**
- ✅ UI hiển thị stopLine (đỏ)
- ✅ UI hiển thị lineB (xanh, gạch gạch)
- ✅ Database có cả `stopLine` và `lineB`

**Backend logs:**
```
✓ Phát hiện vạch dừng: [...]
✓ Tính lineB thành công: [...]
📦 Payload nhận được: {'stopLine': [...], 'lineB': [...]}
🔧 Update document: {'$set': {'regions.stopLine': [...], 'regions.lineB': [...]}}
✓ Đã cập nhật (modified: 1)
```

### Test 2: Manual detect trong modal

**Steps:**
1. Click vào camera tile
2. Click "Line tự động" trong modal

**Expected:**
- ✅ Vẫn hoạt động như cũ
- ✅ Có cả stopLine và lineB

## Kiểm tra

### 1. UI
```
Khi thêm camera mới:
├ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┤ ← LineB (xanh, gạch) ✅
│    Vùng giám sát     │
├───────────────────────┤ ← StopLine (đỏ, liền) ✅
```

### 2. Database
```javascript
db.cameras.findOne({id: "cam-new"})

// Expected:
{
  regions: {
    stopLine: [
      {x: 0.0, y: 0.608},
      {x: 1.0, y: 0.732}
    ],
    lineB: [              // ✅ Phải có!
      {x: 0.0, y: 0.489},
      {x: 1.0, y: 0.613}
    ]
  }
}
```

### 3. Backend logs
```bash
docker compose logs backend --tail 50 | grep -E "(stopLine|lineB|Payload)"
```

Expected:
```
✓ Phát hiện vạch dừng: [...]
✓ Tính lineB thành công: [...]
📦 Payload nhận được: {'stopLine': [...], 'lineB': [...]}
```

## Cách test ngay

### Option 1: Thêm camera mới
1. Vào Settings
2. Thêm camera với RTSP mới
3. Save
4. Xem camera tile → Đợi stream load
5. Check UI có 2 lines không

### Option 2: Xóa regions của camera hiện tại
```javascript
// Trong browser console
fetch('http://localhost:8000/api/cameras/cam-01/regions', {
  method: 'PUT',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({stopLine: null, lineB: null})
})

// Sau đó reload page để trigger auto detect lại
```

### Option 3: Restart frontend + Clear cache
```bash
docker compose restart frontend

# Trong browser:
Ctrl + Shift + R
```

## Files Changed

1. ✅ `frontend/src/components/CameraTile.tsx` - Thêm xử lý lineB trong auto detect
2. ✅ `frontend/src/components/RegionEditorModal.tsx` - Đã có sẵn (fix trước)

## Summary

### Root Cause
Auto detect (CameraTile) chỉ lấy stopLine, không lấy lineB từ API response

### Fix
Thêm logic lấy lineB từ response và thêm vào payload trước khi lưu DB

### Impact
- ✅ Thêm camera mới → Tự động có cả stopLine và lineB
- ✅ Manual detect → Vẫn hoạt động bình thường
- ✅ Không ảnh hưởng các tính năng khác

## Deployment

```bash
# Đã restart
docker compose restart frontend

# Nếu cần rebuild
docker compose up -d --build frontend
```

## Verification Checklist

- [ ] Clear browser cache (Ctrl + Shift + R)
- [ ] Thêm camera mới hoặc xóa regions hiện tại
- [ ] Đợi auto detect chạy
- [ ] Check UI có 2 lines (đỏ + xanh gạch)
- [ ] Check backend logs có lineB
- [ ] Check database có regions.lineB
- [ ] Test manual detect vẫn hoạt động

---

✅ **Fixed! Cả 2 luồng (auto + manual) đều xử lý lineB đúng rồi!**
