# Logic Filter Nâng Cao - Detection Hierarchy

## Yêu Cầu

### 1. ✅ Đèn giao thông (light_*)
- **Luôn hiển thị** - Cả trong và ngoài ROI
- Classes: `light_green`, `light_red`, `light_yellow`

### 2. ✅ Biển số (license_plate)
- **Chỉ hiển thị** khi nằm trong bbox xe
- Parent classes: `bus`, `car`, `motorcycle`, `truck`

### 3. ✅ Mũ bảo hiểm (helmet, no_helmet)
- **Chỉ hiển thị** khi nằm trong bbox xe máy
- Parent class: `motorcycle`

### 4. ✅ Phương tiện (vehicles)
- Filter theo ROI (như bình thường)
- Classes: `bus`, `car`, `motorcycle`, `truck`

## Visual Logic

```
┌─────────────────────────────────────────┐
│  🚦 light_red (LUÔN HIỆN)               │
│                                         │
│  🚗 [car - NGOÀI ROI]                   │
│     └─ 🔲 plate (KHÔNG HIỆN)           │
│                                         │
├─────────────────────────────────────────┤ ← LineB (ROI bắt đầu)
│ ░ 🚦 light_green (LUÔN HIỆN) ░         │
│ ░                              ░         │
│ ░ 🚗 [car - TRONG ROI]         ░         │
│ ░   └─ 🔲 plate (HIỆN) ✅      ░         │
│ ░                              ░         │
│ ░ 🏍️ [motorcycle - TRONG ROI]  ░         │
│ ░   ├─ 🔲 plate (HIỆN) ✅      ░         │
│ ░   └─ 🪖 helmet (HIỆN) ✅     ░         │
│ ░                              ░         │
└─────────────────────────────────────────┘
```

## Filter Logic Flow

### Step 1: Phân loại detections

```python
TRAFFIC_LIGHTS = {"light_green", "light_red", "light_yellow"}
VEHICLES = {"bus", "car", "motorcycle", "truck"}

# Tách theo loại
lights = []        # Đèn giao thông
vehicles = []      # Phương tiện
plates = []        # Biển số
helmets = []       # Mũ bảo hiểm
others = []        # Còn lại
```

### Step 2: Filter theo hierarchy

```
1. Đèn giao thông → filtered (tất cả)
   ↓
2. Vehicles → filter theo ROI → vehicles_in_roi → filtered
   ↓
3. Plates → check trong vehicles_in_roi → filtered
   ↓
4. Helmets → check trong motorcycles_in_roi → filtered
   ↓
5. Others → filter theo ROI → filtered
```

### Step 3: Nested Detection

**Biển số trong xe:**
```python
for plate in plates:
    for vehicle in vehicles_in_roi:
        if is_bbox_inside_bbox(plate.bbox, vehicle.bbox):
            filtered.append(plate)  # ✅ Hiển thị
            break
```

**Mũ trong xe máy:**
```python
motorcycles = [v for v in vehicles_in_roi if v.class == "motorcycle"]
for helmet in helmets:
    for motorcycle in motorcycles:
        if is_bbox_inside_bbox(helmet.bbox, motorcycle.bbox):
            filtered.append(helmet)  # ✅ Hiển thị
            break
```

## Function: `is_bbox_inside_bbox()`

**Check center của bbox con có nằm trong bbox cha không:**

```python
def is_bbox_inside_bbox(inner_bbox: List[float], outer_bbox: List[float]) -> bool:
    # Center của bbox con
    inner_cx = (inner_bbox[0] + inner_bbox[2]) / 2
    inner_cy = (inner_bbox[1] + inner_bbox[3]) / 2
    
    # Bbox cha
    outer_x1, outer_y1, outer_x2, outer_y2 = outer_bbox
    
    # Check center trong bbox
    return (outer_x1 <= inner_cx <= outer_x2 and 
            outer_y1 <= inner_cy <= outer_y2)
```

**Ví dụ:**

```
Vehicle bbox: [100, 200, 300, 400]
  Center: (200, 300)

Plate bbox: [150, 320, 220, 360]
  Center: (185, 340)
  
Check: 
  100 <= 185 <= 300 ✅
  200 <= 340 <= 400 ✅
  
→ Plate INSIDE vehicle ✅
```

## Test Cases

### Test 1: Đèn giao thông ngoài ROI

**Setup:**
```
ROI: y > 0.5 (nửa dưới màn hình)
Detection: light_red at y=0.2 (ngoài ROI)
```

**Expected:**
- ✅ Đèn vẫn hiển thị bbox
- Logic: `filtered.extend(lights)` - không check ROI

### Test 2: Biển số xe ngoài ROI

**Setup:**
```
ROI: y > 0.5
Detection: 
  - car at y=0.2 (ngoài ROI)
  - license_plate inside car
```

**Expected:**
- ❌ Car không hiển thị (ngoài ROI)
- ❌ Plate không hiển thị (parent không hiển thị)
- Logic: Plate chỉ check trong `vehicles_in_roi`

### Test 3: Biển số xe trong ROI

**Setup:**
```
ROI: y > 0.5
Detection:
  - car at y=0.7 (trong ROI)
  - license_plate inside car
```

**Expected:**
- ✅ Car hiển thị (trong ROI)
- ✅ Plate hiển thị (parent hiển thị + nested)

### Test 4: Mũ bảo hiểm xe máy trong ROI

**Setup:**
```
ROI: y > 0.5
Detection:
  - motorcycle at y=0.7 (trong ROI)
  - helmet inside motorcycle
```

**Expected:**
- ✅ Motorcycle hiển thị (trong ROI)
- ✅ Helmet hiển thị (parent hiển thị + nested)

### Test 5: Mũ bảo hiểm ngoài xe máy

**Setup:**
```
Detection:
  - motorcycle at [100, 200, 200, 400]
  - helmet at [500, 300, 550, 350] (xa xe máy)
```

**Expected:**
- ✅ Motorcycle hiển thị
- ❌ Helmet không hiển thị (không nested)
- Logic: `is_bbox_inside_bbox()` return False

## Edge Cases

### Case 1: Xe ngoài ROI nhưng biển số trong ROI

```
Vehicle bbox: [100, 100, 300, 300] (ngoài ROI)
Plate bbox: [150, 400, 220, 450] (trong ROI, nhưng không trong vehicle!)
```

**Result:**
- ❌ Vehicle không hiển thị (ngoài ROI)
- ❌ Plate không hiển thị (không nested với vehicle hiển thị)

**Logic:**
```python
vehicles_in_filtered = [v for v in vehicles if v in filtered]
# Vehicle không trong filtered → Plate không check
```

### Case 2: Nhiều xe chồng lên nhau

```
car1 at [100, 200, 300, 400]
car2 at [250, 200, 450, 400]
plate at [270, 300, 320, 340]
```

**Result:**
- Plate sẽ được gán cho xe **đầu tiên** match
- Logic: `break` sau khi tìm thấy parent đầu tiên

### Case 3: Helmet không có xe máy

```
helmet at [100, 200, 150, 250]
No motorcycle detected
```

**Result:**
- ❌ Helmet không hiển thị
- Logic: Không có parent motorcycle → không match

## Performance

### Độ phức tạp

**Trước (Simple ROI filter):**
```
O(n) với n = số detections
```

**Sau (Hierarchy filter):**
```
O(n + m*k) với:
  n = số detections
  m = số plates/helmets
  k = số vehicles/motorcycles (thường k << n)
  
Worst case: O(n²) nếu tất cả là nested detections
Best case: O(n) nếu không có nested
```

**Thực tế:**
- Số plates, helmets thường rất ít (~1-3 per frame)
- Overhead: ~1-2ms per frame

## Logging

**Debug nested detection:**
```python
# Trong filter_detections_by_roi()
logger.debug(f"Lights: {len(lights)}, always shown")
logger.debug(f"Vehicles in ROI: {len(vehicles_in_roi)}/{len(vehicles)}")
logger.debug(f"Plates shown: {plates_shown}/{len(plates)}")
logger.debug(f"Helmets shown: {helmets_shown}/{len(helmets)}")
```

## Database Impact

**Không ảnh hưởng database.**

ROI vẫn lưu như cũ:
```javascript
{
  regions: {
    stopLine: [...],
    lineB: [...],
    roi: [...]  // Dùng để filter vehicles
  }
}
```

## Summary

### ✅ Logic mới

| Class | Filter Logic |
|-------|-------------|
| `light_*` | Luôn hiển thị (cả ngoài ROI) |
| `bus/car/motorcycle/truck` | Filter theo ROI |
| `license_plate` | Nested trong vehicles (đã filter ROI) |
| `helmet/no_helmet` | Nested trong motorcycles (đã filter ROI) |
| Others | Filter theo ROI |

### 📊 Workflow

```
ALL Detections
    ↓
Classify (lights, vehicles, plates, helmets, others)
    ↓
Filter:
  1. Lights → filtered (all)
  2. Vehicles → filter ROI → filtered
  3. Plates → check nested in filtered vehicles → filtered
  4. Helmets → check nested in filtered motorcycles → filtered
  5. Others → filter ROI → filtered
    ↓
Draw filtered detections
```

### 🎯 Benefits

- **UI sạch sẽ**: Chỉ hiện detections có ý nghĩa
- **Logic đúng**: Plate/helmet chỉ hiện khi có parent
- **Đèn giao thông**: Luôn quan trọng, luôn hiển thị
- **Performance**: Overhead nhỏ (~1-2ms)

---

**Filter hierarchy hoàn tất!** 🎉
