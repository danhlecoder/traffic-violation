# Fix: LineB không hiển thị và lưu trong Database

## Vấn đề

Backend đã trả về `lineB` trong response nhưng:
- Frontend không hiển thị lineB trên UI
- Database không lưu lineB

## Nguyên nhân

Frontend chưa được cập nhật để xử lý field `lineB`:
1. Type definition không có `lineB`
2. Component `RegionOverlay` không vẽ `lineB`
3. Component `RegionEditorModal` không lưu `lineB` sau khi detect
4. Store `useStore` không hỗ trợ clear `lineB`

## Giải pháp

### 1. Cập nhật Type Definition

**File:** `frontend/src/types/regions.ts`

```typescript
export interface CameraRegion {
  stopLine?: [Point, Point]
  lineB?: [Point, Point]     // ← ADDED
  roi?: Point[]
}
```

### 2. Cập nhật RegionOverlay - Vẽ lineB

**File:** `frontend/src/components/RegionOverlay.tsx`

**Thêm code vẽ lineB:**
```tsx
{region?.lineB && (
  <svg className="region-svg">
    {(() => {
      const [a, b] = region.lineB!
      const A = toPixel(a)
      const B = toPixel(b)
      return (
        <g>
          <line 
            x1={A.x} y1={A.y} 
            x2={B.x} y2={B.y} 
            className="region-line" 
            style={{ 
              stroke: '#10b981',        // Màu xanh lá
              strokeWidth: 2, 
              strokeDasharray: '5,5'    // Đường gạch gạch
            }} 
          />
          <circle cx={A.x} cy={A.y} r={4} style={{ fill: '#10b981' }} />
          <circle cx={B.x} cy={B.y} r={4} style={{ fill: '#10b981' }} />
        </g>
      )
    })()}
  </svg>
)}
```

**Style:**
- LineB: Màu xanh lá `#10b981`, đường gạch gạch
- StopLine: Màu đỏ (như cũ), đường liền

### 3. Cập nhật RegionEditorModal - Lưu lineB

**File:** `frontend/src/components/RegionEditorModal.tsx`

**Thay đổi logic sau khi detect:**

```typescript
// TRƯỚC
const line = data?.stopLine
if (line && line.length === 2) {
  const payload = { stopLine: line as any }
  setCameraRegion(cameraId, payload)
  await streams.updateCameraRegions(cameraId, payload)
  message.success('Đã phát hiện và lưu vạch dừng')
}

// SAU
const line = data?.stopLine
const lineB = data?.lineB
if (line && line.length === 2) {
  const payload: any = { stopLine: line }
  if (lineB && lineB.length === 2) {
    payload.lineB = lineB    // ← ADDED
  }
  setCameraRegion(cameraId, payload)
  await streams.updateCameraRegions(cameraId, payload)
  message.success(lineB ? 'Đã phát hiện và lưu stopLine + lineB' : 'Đã phát hiện và lưu vạch dừng')
}
```

**Thêm nút xóa lineB:**

```tsx
{cameraRegion.lineB && (
  <Tooltip title="Xóa lineB">
    <Button
      size="small"
      danger
      icon={<ClearOutlined />}
      onClick={async () => {
        clearCameraRegion(cameraId, 'lineB')
        try { await streams.updateCameraRegions(cameraId, { lineB: null }) } catch {}
      }}
    >Xóa lineB</Button>
  </Tooltip>
)}
```

### 4. Cập nhật Store - Support clear lineB

**File:** `frontend/src/store/useStore.ts`

**Cập nhật type:**
```typescript
clearCameraRegion: (cameraId: string, target?: 'stopLine' | 'lineB' | 'roi' | 'all') => void
```

**Cập nhật implementation:**
```typescript
clearCameraRegion: (cameraId, target) => set((s) => {
  const map = { ...(s.settings.cameraRegions || {}) }
  if (!target || target === 'all') {
    delete map[cameraId]
  } else {
    const prev = map[cameraId]
    if (prev) {
      const updated: CameraRegion = { ...prev }
      if (target === 'stopLine') delete (updated as any).stopLine
      if (target === 'lineB') delete (updated as any).lineB    // ← ADDED
      if (target === 'roi') delete (updated as any).roi
      map[cameraId] = updated
    }
  }
  // ... lưu vào localStorage
}),
```

## Rebuild & Deploy

```bash
# Restart frontend container
docker compose restart frontend
```

## Kết quả

### UI Hiển thị

- **StopLine**: Đường màu đỏ (như cũ)
- **LineB**: Đường màu xanh lá, gạch gạch, phía trên stopLine 64px

### Database

```json
{
  "_id": "ObjectId('...')",
  "id": "cam-01",
  "name": "Camera mới",
  "regions": {
    "stopLine": [
      {"x": 0.0, "y": 0.667},
      {"x": 1.0, "y": 0.667}
    ],
    "lineB": [
      {"x": 0.0, "y": 0.578},
      {"x": 1.0, "y": 0.578}
    ]
  }
}
```

### API Response

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

## Testing

### Test 1: Auto Detect

1. Mở modal "Thiết lập vùng"
2. Click "Line tự động"
3. Kiểm tra:
   - ✅ Hiển thị stopLine (đỏ)
   - ✅ Hiển thị lineB (xanh, gạch gạch)
   - ✅ Message: "Đã phát hiện và lưu stopLine + lineB"

### Test 2: Database Storage

1. Sau khi detect, check database:
```bash
db.cameras.findOne({id: "cam-01"})
```

2. Kiểm tra có field `regions.lineB` không

### Test 3: Xóa lineB

1. Click nút "Xóa lineB"
2. Kiểm tra:
   - ✅ LineB biến mất trên UI
   - ✅ Database không còn field `lineB`
   - ✅ StopLine vẫn còn

## Visual Comparison

### Trước (Chỉ có StopLine)
```
┌────────────────────────────────────┐
│                                    │
│                                    │
│                                    │
├────────────────────────────────────┤ ← StopLine (đỏ)
│                                    │
└────────────────────────────────────┘
```

### Sau (Có cả LineB)
```
┌────────────────────────────────────┐
│                                    │
├ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┤ ← LineB (xanh, gạch) 64px
│        [Vùng giám sát]             │
├────────────────────────────────────┤ ← StopLine (đỏ, liền)
│                                    │
└────────────────────────────────────┘
```

## Files Changed

### Frontend
1. `src/types/regions.ts` - Thêm `lineB` vào interface
2. `src/components/RegionOverlay.tsx` - Vẽ lineB
3. `src/components/RegionEditorModal.tsx` - Lưu lineB & thêm nút xóa
4. `src/store/useStore.ts` - Support clear lineB

### Backend (Đã có sẵn)
- `backend/schemas/camera.py` - Đã có field `lineB`
- `backend/services/detect_line.py` - Đã có function tính lineB
- `backend/api/streams.py` - Đã trả về lineB

## Notes

- **Màu sắc**: StopLine (đỏ), LineB (xanh lá)
- **Style**: StopLine (liền), LineB (gạch gạch)
- **Offset**: LineB nằm phía trên stopLine 64px
- **Auto detect**: Backend tự động tính và trả về cả 2 lines
- **Database**: Lưu đồng thời stopLine và lineB

## Troubleshooting

### LineB không hiển thị
1. Check console có lỗi TypeScript không
2. Clear browser cache
3. Restart frontend container

### LineB không lưu vào DB
1. Check API response có `lineB` không
2. Check backend logs
3. Verify schema có field `lineB`

### Style không đúng
1. Check CSS class `.region-line`
2. Inline style có override không
3. Browser DevTools kiểm tra computed style

## Success Criteria

- [x] LineB hiển thị trên UI (màu xanh, gạch gạch)
- [x] LineB được lưu vào database
- [x] Có thể xóa lineB độc lập
- [x] Message thông báo đúng
- [x] Không ảnh hưởng stopLine và ROI
- [x] TypeScript không báo lỗi
