# Test Ngay - Đã Thêm Debug Logs

## Vấn đề tìm thấy

Từ logs backend:
```
✓ Tính lineB thành công: [...]              ✅ Backend OK
📦 Payload nhận được: {'stopLine': (...)}   ❌ Frontend KHÔNG gửi lineB!
```

**Frontend không gửi `lineB` trong PUT request!**

## Đã fix

1. ✅ Thêm console.log để debug
2. ✅ Rebuild frontend với code mới

## Test ngay (QUAN TRỌNG!)

### Bước 1: Hard refresh browser
```
Ctrl + Shift + Delete
→ Chọn: Cached images and files
→ Time range: All time
→ Clear data

Sau đó: Ctrl + F5 để reload
```

### Bước 2: Mở Browser Console
```
F12 → Console tab
```

### Bước 3: Test auto detect
1. Click "Line tự động"
2. Xem console logs:

**Expected:**
```javascript
🎯 Response data: {stopLine: [...], lineB: [...]}
📍 lineB: [{x: 0.0, y: 0.489}, {x: 0.999, y: 0.613}]
📦 Payload sẽ gửi: {stopLine: [...], lineB: [...]}
```

**Nếu không thấy lineB:**
```javascript
🎯 Response data: {stopLine: [...]}  // ❌ Backend không trả lineB
📍 lineB: undefined                  // ❌ lineB là undefined
📦 Payload sẽ gửi: {stopLine: [...]} // ❌ Không có lineB
```

### Bước 4: Check backend logs
```bash
docker compose logs backend --tail 30
```

**Expected:**
```
✓ Tính lineB thành công: [...]
📦 Payload nhận được: {'stopLine': [...], 'lineB': [...]}  ← Phải có lineB!
🔧 Update document: {'$set': {'regions.stopLine': [...], 'regions.lineB': [...]}}
✓ Đã cập nhật (modified: 1)
```

### Bước 5: Check UI
- Phải thấy **2 lines**:
  - StopLine: Màu đỏ (liền)
  - LineB: Màu xanh lá (gạch gạch) phía trên

## Nếu vẫn không work

### Scenario 1: Console không có logs
**Problem:** Code cũ vẫn đang chạy
**Fix:**
```bash
# Clear browser cache hoàn toàn
# Hoặc thử incognito mode
```

### Scenario 2: lineB = undefined
**Problem:** Backend response không có lineB
**Fix:** Check backend code có return lineB không

### Scenario 3: Payload không có lineB
**Problem:** Logic `if (lineB && lineB.length === 2)` fail
**Fix:** 
```typescript
// lineB có thể là array of objects thay vì tuple
// Check: lineB = [{x, y}, {x, y}] thay vì [[x,y], [x,y]]
```

## Debug Commands

### 1. Check response từ backend
```bash
curl -X POST http://localhost:8000/api/detect/stopline \
  -H "Content-Type: application/json" \
  -d '{"image": "data:image/jpeg;base64,..."}' \
  | jq '.lineB'
```

### 2. Check database
```bash
docker compose exec mongo mongosh

use traffic_violations
db.cameras.findOne({id: "cam-01"}, {regions: 1})
```

### 3. Watch logs real-time
```bash
docker compose logs -f backend | grep -E "(lineB|Payload|Update)"
```

## Screenshots cần gửi

Nếu vẫn không work, gửi:
1. **Browser Console** (F12) - Toàn bộ logs
2. **Backend logs** - 50 dòng cuối
3. **Network tab** - Request/Response của PUT /api/cameras/*/regions
4. **Database** - Output của `db.cameras.findOne({id: "cam-01"})`

## Expected Working State

### Browser Console
```javascript
🎯 Response data: {
  stopLine: [{x: 0, y: 0.608}, {x: 0.999, y: 0.732}],
  lineB: [{x: 0, y: 0.489}, {x: 0.999, y: 0.613}]
}
📍 lineB: [{x: 0, y: 0.489}, {x: 0.999, y: 0.613}]
📦 Payload sẽ gửi: {
  stopLine: [...],
  lineB: [...]
}
```

### Backend Logs
```
✓ Tính lineB thành công
📦 Payload nhận được: {'stopLine': [...], 'lineB': [...]}
🔧 Update document: {'$set': {'regions.stopLine': [...], 'regions.lineB': [...]}}
✓ Đã cập nhật (modified: 1)
```

### Database
```javascript
{
  "_id": ObjectId("..."),
  "regions": {
    "stopLine": [
      {"x": 0.0, "y": 0.608},
      {"x": 0.999, "y": 0.732}
    ],
    "lineB": [
      {"x": 0.0, "y": 0.489},
      {"x": 0.999, "y": 0.613}
    ]
  }
}
```

### UI
- Line đỏ (stopLine) ✅
- Line xanh gạch gạch (lineB) phía trên ✅

---

## TEST NGAY! 🚀

1. Clear browser cache hoàn toàn
2. F5 reload page
3. F12 mở console
4. Click "Line tự động"
5. Check console logs
6. Gửi lại screenshots!
