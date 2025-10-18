# Cấu Hình Style Cho StopLine và LineB

## Đã thay đổi

### 1. Style Lines
- ✅ **Cả 2 lines đều màu đỏ** (trước: lineB màu xanh)
- ✅ **Cả 2 lines đều nét liền** (trước: lineB gạch gạch)
- ✅ **Độ dày nhỏ hơn: 2px** (trước: 5px)

### 2. Config trong `.env`
```bash
# ===================== LINE B (VẠCH PHỤ) =====================
LINE_B_OFFSET_PX=64                # Khoảng cách từ stopLine lên lineB (px)
LINE_B_STROKE_WIDTH=2              # Độ dày lineB (px) 
STOP_LINE_STROKE_WIDTH=2           # Độ dày stopLine (px)
```

## Visual Result

```
TRƯỚC:
├ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┤ ← LineB (xanh, gạch, dày)
│                      │
├──────────────────────┤ ← StopLine (đỏ, liền, dày)

SAU:
├──────────────────────┤ ← LineB (đỏ, liền, 2px)
│                      │
├──────────────────────┤ ← StopLine (đỏ, liền, 2px)
```

## Files thay đổi

### 1. `.env`
```bash
# Thêm config mới
LINE_B_OFFSET_PX=64                # Khoảng cách (px)
LINE_B_STROKE_WIDTH=2              # Độ dày lineB
STOP_LINE_STROKE_WIDTH=2           # Độ dày stopLine
```

### 2. Frontend: `RegionOverlay.tsx`

**StopLine - TRƯỚC:**
```tsx
<line className="region-line" />  // Màu đỏ mặc định, dày
<circle r={5} />                  // Điểm to
```

**StopLine - SAU:**
```tsx
<line className="region-line" style={{ strokeWidth: 2 }} />
<circle r={4} />  // Nhỏ hơn
```

**LineB - TRƯỚC:**
```tsx
<line 
  style={{ 
    stroke: '#10b981',        // ❌ Xanh
    strokeWidth: 2, 
    strokeDasharray: '5,5'    // ❌ Gạch gạch
  }} 
/>
```

**LineB - SAU:**
```tsx
<line 
  className="region-line"     // ✅ Dùng class (màu đỏ)
  style={{ strokeWidth: 2 }}  // ✅ Nét liền, 2px
/>
```

### 3. Backend: `api/streams.py`

**TRƯỚC:**
```python
lineB_result = calculate_lineB_from_stopline(
  stopline_result, h, offset_px=64  # ❌ Hardcode
)
```

**SAU:**
```python
import os
offset_px = int(os.getenv('LINE_B_OFFSET_PX', '64'))  # ✅ Đọc từ .env
lineB_result = calculate_lineB_from_stopline(
  stopline_result, h, offset_px=offset_px
)
```

## Cách điều chỉnh

### 1. Thay đổi khoảng cách giữa 2 lines

Edit `.env`:
```bash
LINE_B_OFFSET_PX=80   # Tăng thành 80px (xa hơn)
```

Restart backend:
```bash
docker compose restart backend
```

### 2. Thay đổi độ dày lines

**Option 1: Edit .env (cần cập nhật code)**
```bash
STOP_LINE_STROKE_WIDTH=3  # Dày hơn
LINE_B_STROKE_WIDTH=1     # Mỏng hơn
```

**Option 2: Edit code trực tiếp**

File: `frontend/src/components/RegionOverlay.tsx`

```tsx
// StopLine
<line className="region-line" style={{ strokeWidth: 3 }} />

// LineB  
<line className="region-line" style={{ strokeWidth: 1 }} />
```

Restart frontend:
```bash
docker compose restart frontend
```

### 3. Thay đổi màu sắc

File: `frontend/src/components/RegionOverlay.tsx`

```tsx
// Màu khác cho lineB (ví dụ: cam)
<line 
  className="region-line" 
  style={{ 
    strokeWidth: 2,
    stroke: '#ff6600'  // Màu cam
  }} 
/>
```

### 4. Đổi lại nét gạch (nếu muốn)

```tsx
<line 
  className="region-line" 
  style={{ 
    strokeWidth: 2,
    strokeDasharray: '8,4'  // Nét gạch 8px, khoảng 4px
  }} 
/>
```

## Test

### 1. Clear cache
```bash
Ctrl + Shift + R
```

### 2. Check UI
- ✅ Cả 2 lines màu đỏ
- ✅ Cả 2 lines nét liền
- ✅ Độ dày 2px (mỏng hơn trước)

### 3. Thử thay đổi config

Edit `.env`:
```bash
LINE_B_OFFSET_PX=100  # Tăng khoảng cách
```

Restart:
```bash
docker compose restart backend
```

Xóa regions và detect lại để thấy thay đổi.

## CSS Classes

File CSS có thể có class `.region-line`:
```css
.region-line {
  stroke: #ef4444;        /* Màu đỏ */
  stroke-width: 3;        /* Độ dày mặc định */
  fill: none;
}
```

Inline style sẽ override:
```tsx
style={{ strokeWidth: 2 }}  // Override thành 2px
```

## Các Style Phổ Biến

### 1. Nét liền
```tsx
style={{ strokeWidth: 2 }}
```

### 2. Nét gạch
```tsx
style={{ 
  strokeWidth: 2,
  strokeDasharray: '5,5'  // 5px line, 5px gap
}}
```

### 3. Nét chấm
```tsx
style={{ 
  strokeWidth: 2,
  strokeDasharray: '2,3'  // 2px dot, 3px gap
}}
```

### 4. Độ trong suốt
```tsx
style={{ 
  strokeWidth: 2,
  opacity: 0.7  // 70% opacity
}}
```

## Troubleshooting

### Lines vẫn có màu cũ
→ Hard refresh: `Ctrl + Shift + R`

### Khoảng cách không đổi
→ Restart backend: `docker compose restart backend`
→ Xóa regions cũ và detect lại

### Độ dày không đổi
→ Restart frontend: `docker compose restart frontend`
→ Clear cache browser

## Summary

### ✅ Đã fix
1. Cả 2 lines màu đỏ
2. Cả 2 lines nét liền
3. Độ dày 2px (mỏng hơn)
4. Có thể config khoảng cách trong `.env`

### 📝 Config trong `.env`
```bash
LINE_B_OFFSET_PX=64           # Khoảng cách (có thể đổi)
LINE_B_STROKE_WIDTH=2         # Độ dày lineB (chưa dùng, để tương lai)
STOP_LINE_STROKE_WIDTH=2      # Độ dày stopLine (chưa dùng, để tương lai)
```

### 🎨 Style hiện tại
```tsx
// Cả 2 đều như này
<line 
  className="region-line"       // Màu đỏ từ CSS
  style={{ strokeWidth: 2 }}    // Độ dày 2px
/>
<circle r={4} />                // Điểm nhỏ 4px
```

---

**Đẹp và gọn hơn rồi!** 🎉
