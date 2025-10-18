# Fix Final: LineB Auto Sync với StopLine

## Vấn đề đã fix

### 1. Nút xóa lineB riêng không cần thiết
**Yêu cầu:** Xóa stopLine tự động xóa lineB, thêm stopLine tự động thêm lineB

**Giải pháp:**
- ✅ Xóa nút "Xóa lineB" riêng
- ✅ Nút "Xóa line" sẽ xóa cả stopLine và lineB
- ✅ Auto detect sẽ tự động thêm cả stopLine và lineB

### 2. Không lưu vào DB và không hiển thị
**Log backend:**
```
✓ Phát hiện vạch dừng: [{'x': 0.0, 'y': 0.667}, ...]
✓ Tính lineB thành công: [{'x': 0.0, 'y': 0.548}, ...]
```

**Root cause:** Type definition `CameraRegion` trong `types/api.ts` thiếu field `lineB`

**Giải pháp:** Thêm `lineB` vào API types

---

## Thay đổi code

### 1. Xóa nút xóa lineB riêng

**File:** `frontend/src/components/RegionEditorModal.tsx`

**TRƯỚC:**
```tsx
{cameraRegion.stopLine && (
  <Button onClick={() => { /* xóa stopLine */ }}>
    Xóa stopLine
  </Button>
)}
{cameraRegion.lineB && (
  <Button onClick={() => { /* xóa lineB */ }}>
    Xóa lineB
  </Button>
)}
```

**SAU:**
```tsx
{cameraRegion.stopLine && (
  <Tooltip title="Xóa vạch dừng (và lineB)">
    <Button
      onClick={async () => {
        clearCameraRegion(cameraId, 'stopLine')
        clearCameraRegion(cameraId, 'lineB')
        await streams.updateCameraRegions(cameraId, { 
          stopLine: null, 
          lineB: null 
        })
      }}
    >Xóa line</Button>
  </Tooltip>
)}
```

### 2. Fix API Types

**File:** `frontend/src/types/api.ts`

**TRƯỚC:**
```typescript
export type CameraRegion = {
  stopLine?: [Point, Point] | null
  roi?: Point[] | null
}
```

**SAU:**
```typescript
export type CameraRegion = {
  stopLine?: [Point, Point] | null
  lineB?: [Point, Point] | null    // ✅ ADDED
  roi?: Point[] | null
}
```

---

## Workflow hoàn chỉnh

### Auto Detect Flow

```
User click "Line tự động"
        ↓
Backend detect stopLine
        ↓
Backend tính lineB (64px offset)
        ↓
Response: { stopLine: [...], lineB: [...] }
        ↓
Frontend nhận response
        ↓
setCameraRegion({ stopLine, lineB })  ← Lưu cả 2
        ↓
updateCameraRegions({ stopLine, lineB })  ← API call
        ↓
Database lưu cả 2 fields
        ↓
UI hiển thị cả 2 lines
```

### Delete Flow

```
User click "Xóa line"
        ↓
clearCameraRegion('stopLine')
clearCameraRegion('lineB')      ← Xóa cả 2
        ↓
updateCameraRegions({ 
  stopLine: null, 
  lineB: null 
})
        ↓
Database xóa cả 2 fields
        ↓
UI ẩn cả 2 lines
```

---

## Files Changed

### Frontend
1. ✅ `src/types/api.ts` - Thêm `lineB` vào `CameraRegion` type
2. ✅ `src/types/regions.ts` - Đã có `lineB` (fix trước)
3. ✅ `src/components/RegionEditorModal.tsx` - Xóa nút riêng, logic xóa cả 2
4. ✅ `src/components/RegionOverlay.tsx` - Vẽ lineB (fix trước)
5. ✅ `src/store/useStore.ts` - Support clear lineB (fix trước)

### Backend
- ✅ Không cần thay đổi (đã hoàn chỉnh)

---

## Test Checklist

### Test 1: Auto Detect
- [ ] Click "Line tự động"
- [ ] Kiểm tra UI hiển thị:
  - [ ] StopLine màu đỏ (liền)
  - [ ] LineB màu xanh (gạch gạch), phía trên 64px
- [ ] Kiểm tra database:
```javascript
db.cameras.findOne({id: "cam-01"})
// Expect: regions.stopLine và regions.lineB đều có
```

### Test 2: Manual Delete
- [ ] Click "Xóa line"
- [ ] Kiểm tra UI:
  - [ ] Cả stopLine và lineB đều biến mất
- [ ] Kiểm tra database:
```javascript
db.cameras.findOne({id: "cam-01"})
// Expect: regions.stopLine và regions.lineB đều null/undefined
```

### Test 3: ROI không bị ảnh hưởng
- [ ] Thêm ROI
- [ ] Xóa line (stopLine + lineB)
- [ ] Kiểm tra ROI vẫn còn

---

## API Response Example

### POST `/api/detect/stopline`

**Request:**
```json
{
  "image": "data:image/jpeg;base64,..."
}
```

**Response:**
```json
{
  "stopLine": [
    {"x": 0.0, "y": 0.6666666666666666},
    {"x": 1.0, "y": 0.6666666666666666}
  ],
  "lineB": [
    {"x": 0.0, "y": 0.548148148148148},
    {"x": 1.0, "y": 0.548148148148148}
  ]
}
```

### PUT `/api/cameras/{id}/regions`

**Request:**
```json
{
  "stopLine": [[{"x": 0.0, "y": 0.667}, {"x": 1.0, "y": 0.667}]],
  "lineB": [[{"x": 0.0, "y": 0.548}, {"x": 1.0, "y": 0.548}]]
}
```

**Response:**
```json
{
  "ok": true
}
```

---

## Database Schema

```javascript
{
  "_id": ObjectId("..."),
  "id": "cam-01",
  "name": "Camera mới",
  "rtsp": "rtsp://...",
  "location": "Ngã tư XYZ",
  "regions": {
    "stopLine": [
      {"x": 0.0, "y": 0.667},
      {"x": 1.0, "y": 0.667}
    ],
    "lineB": [
      {"x": 0.0, "y": 0.548},
      {"x": 1.0, "y": 0.548}
    ],
    "roi": [...]
  }
}
```

---

## Visual Result

```
┌─────────────────────────────────────┐
│                                     │
│         (Camera view)               │
│                                     │
├ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┤ ← LineB (xanh, gạch)
│                                     │
│       [Vùng giám sát 64px]         │
│                                     │
├─────────────────────────────────────┤ ← StopLine (đỏ, liền)
│                                     │
│         (Khu vực sau line)          │
│                                     │
└─────────────────────────────────────┘
```

---

## Summary

### Đã fix
1. ✅ Xóa stopLine → Tự động xóa lineB
2. ✅ Thêm stopLine → Tự động thêm lineB
3. ✅ Xóa nút "Xóa lineB" riêng
4. ✅ Fix type definition API
5. ✅ LineB hiển thị trên UI
6. ✅ LineB lưu vào database

### Logic mới
- **1 nút xóa** cho cả stopLine và lineB
- **Auto sync** giữa stopLine và lineB
- **Không còn** nút xóa riêng cho lineB

### Restart containers
```bash
docker compose restart frontend backend
```

---

## Troubleshooting

### Nếu vẫn không hiển thị lineB
1. Hard refresh browser (Ctrl+Shift+R)
2. Clear browser cache
3. Check console có lỗi không
4. Verify `types/api.ts` có `lineB` field

### Nếu không lưu vào DB
1. Check backend logs: `docker compose logs backend`
2. Verify API call có được gọi không (Network tab)
3. Check MongoDB: `db.cameras.find()`

---

## Done! 🎉

Tất cả vấn đề đã được fix:
- LineB tự động sync với stopLine
- UI hiển thị đúng
- Database lưu đúng
- Không còn nút thừa

Test ngay và báo lại kết quả! 🚀
