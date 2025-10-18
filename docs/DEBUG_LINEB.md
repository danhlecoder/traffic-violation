# Debug: LineB không lưu vào Database

## Đã thêm logs để debug

### Backend logs mới
1. `📦 Payload nhận được:` - Xem frontend gửi gì lên
2. `🔧 Update document:` - Xem MongoDB query như thế nào
3. `✓ Đã cập nhật regions (modified: X)` - Xem có update được không

## Cách test

### Bước 1: Clear browser cache
```bash
# Trong browser
Ctrl + Shift + R (hard refresh)
# hoặc
Ctrl + Shift + Delete → Clear cache
```

### Bước 2: Test auto detect
1. Mở modal "Thiết lập vùng"
2. Click "Line tự động"
3. Xem message có hiển thị "Đã phát hiện và lưu stopLine + lineB" không

### Bước 3: Xem backend logs
```bash
docker compose logs backend --tail 50
```

**Expect logs:**
```
✓ Phát hiện vạch dừng: [{'x': 0.0, 'y': 0.667}, ...]
✓ Tính lineB thành công: [{'x': 0.0, 'y': 0.548}, ...]
📦 Payload nhận được: {'stopLine': [...], 'lineB': [...]}
🔧 Update document: {'$set': {'regions.stopLine': [...], 'regions.lineB': [...]}}
✓ Đã cập nhật regions cho camera: cam-01 (modified: 1)
```

### Bước 4: Check database
```javascript
db.cameras.findOne({id: "cam-01"})
```

**Expect:**
```javascript
{
  regions: {
    stopLine: [...],
    lineB: [...]  // ← Phải có field này
  }
}
```

## Các trường hợp có thể xảy ra

### Case 1: Payload không có lineB
```
📦 Payload nhận được: {'stopLine': [...]}  // ❌ Thiếu lineB
```

**Nguyên nhân:** Frontend không gửi lineB
**Fix:** Check browser console có lỗi TypeScript không

### Case 2: Update document không có lineB
```
📦 Payload nhận được: {'stopLine': [...], 'lineB': [...]}  // ✅ Có
🔧 Update document: {'$set': {'regions.stopLine': [...]}}  // ❌ Thiếu lineB
```

**Nguyên nhân:** Backend filter ra lineB
**Fix:** Check schema validation

### Case 3: Modified count = 0
```
✓ Đã cập nhật regions (modified: 0)  // ❌ Không update
```

**Nguyên nhân:** Camera không tồn tại hoặc giá trị trùng
**Fix:** Check camera ID có đúng không

## Quick Fix Commands

### 1. Restart tất cả
```bash
docker compose restart frontend backend
```

### 2. Rebuild frontend
```bash
docker compose up -d --build frontend
```

### 3. Clear browser completely
```bash
# Chrome/Edge
Ctrl + Shift + Delete
→ Clear: Cached images and files
→ Time range: All time
```

### 4. Check MongoDB directly
```bash
docker compose exec mongo mongosh

use traffic_violations
db.cameras.find({id: "cam-01"}).pretty()
```

## Files đã modify

1. ✅ `backend/api/cameras.py` - Thêm debug logs
2. ✅ `frontend/src/types/api.ts` - Đã có lineB
3. ✅ `frontend/src/components/RegionEditorModal.tsx` - Đã lưu lineB

## Next Steps

1. **Hard refresh browser** (Ctrl+Shift+R)
2. **Test lại** auto detect
3. **Copy logs** và gửi lại để phân tích
4. **Check database** xem có lineB chưa

## Expected Working Flow

```
User: Click "Line tự động"
     ↓
Frontend: POST /api/detect/stopline
     ↓
Backend: Detect → Response { stopLine: [...], lineB: [...] }
     ↓
Frontend: Nhận response
     ↓
Frontend: Log console.log(data.lineB) → Phải có giá trị
     ↓
Frontend: PUT /api/cameras/{id}/regions với { stopLine, lineB }
     ↓
Backend Log: 📦 Payload nhận được: {stopLine: [...], lineB: [...]}
     ↓
Backend Log: 🔧 Update document: {'$set': {'regions.stopLine': [...], 'regions.lineB': [...]}}
     ↓
Backend Log: ✓ Đã cập nhật (modified: 1)
     ↓
Database: regions.lineB được lưu
     ↓
Frontend: UI hiển thị lineB màu xanh
```

## Test Checklist

- [ ] Browser đã hard refresh (Ctrl+Shift+R)
- [ ] Click "Line tự động"
- [ ] Thấy message "Đã phát hiện và lưu stopLine + lineB"
- [ ] Backend logs có `📦 Payload nhận được`
- [ ] Backend logs có `🔧 Update document`
- [ ] Backend logs có `modified: 1`
- [ ] Database có field `regions.lineB`
- [ ] UI hiển thị lineB màu xanh gạch gạch

## Nếu vẫn không work

Gửi lại:
1. Backend logs (từ detect đến update)
2. Browser console logs (F12)
3. Network tab screenshot (request/response)
4. Database screenshot
