# 🎯 OBJECT TRACKING - PROMPT

## 📋 Metadata
```yaml
tags: [detection, tracking, deepsort, multi-object]
inputs:
  - detections (bboxes từ YOLO)
  - frame (numpy array)
  - camera_id
tools:
  - DeepSORT
  - OpenCV
  - numpy
output_format: Tracked objects với IDs
complexity: High
```

---

## 🎯 Chức năng

### Module: Vehicle Tracker
**Mục đích**: Track xe qua nhiều frames, gán persistent IDs

**Vị trí files**:
- `backend/core/tracking/vehicle_tracker.py` - Core tracker
- `backend/core/tracking/roi_entry_tracker.py` - ROI entry tracking
- `backend/core/tracking/stopline_tracker.py` - Stop line violations

**Pipeline**:
1. Nhận detections từ YOLO (frame t)
2. Match với tracked objects (frame t-1)
3. Update existing tracks
4. Create new tracks cho unmatched detections
5. Delete lost tracks
6. Return tracked objects với IDs

---

## ✅ Checklist Tracking Flow

### 1. Initialization
- [ ] Load DeepSORT model
- [ ] Configure tracking parameters
- [ ] Set IOU threshold (default: 0.3)
- [ ] Set max_age (frames before deletion)
- [ ] Set min_hits (frames before confirmed)

### 2. Detection Processing
- [ ] Convert YOLO detections sang tracking format
- [ ] Filter low confidence detections
- [ ] Extract appearance features (nếu dùng deep features)
- [ ] Prepare bboxes [x1,y1,x2,y2]

### 3. Matching
- [ ] Predict positions của existing tracks
- [ ] Compute IOU giữa predictions và detections
- [ ] Hungarian algorithm matching
- [ ] Handle occlusions
- [ ] Handle ID switches

### 4. Track Update
- [ ] Update matched tracks với new detections
- [ ] Increment age của unmatched tracks
- [ ] Create new tracks cho unmatched detections
- [ ] Delete tracks exceed max_age

### 5. ROI Tracking
- [ ] Check tracked objects vào/ra ROI
- [ ] Log entry/exit events
- [ ] Trigger violation checks
- [ ] Update object metadata

### 6. State Management
- [ ] Track state: Tentative → Confirmed → Deleted
- [ ] Track history (trajectory)
- [ ] Track attributes (color, type, plate)
- [ ] Track violations

---

## ⚠️ Pitfalls - Lỗi thường gặp

### 1. IOU Threshold không phù hợp
❌ **Sai**: IOU threshold quá cao (0.8)
- Kết quả: Tạo nhiều tracks mới cho cùng object

✅ **Đúng**: IOU threshold 0.3-0.5 cho vehicles

### 2. Không handle occlusions
❌ **Sai**: Delete track ngay khi không detect
- Kết quả: ID switches khi xe bị che khuất

✅ **Đúng**: max_age=30 frames để handle temporary occlusion

### 3. Tracking mọi object
❌ **Sai**: Track cả người đi bộ, xe đạp không cần
- Kết quả: Waste resources, chậm

✅ **Đúng**: Filter chỉ track vehicle classes cần thiết

### 4. Không manage tracker instances
❌ **Sai**: Tạo tracker mới mỗi frame
- Kết quả: Mất track history, ID không persistent

✅ **Đúng**: 1 tracker instance per camera, reuse

### 5. Memory leak từ track history
❌ **Sai**: Lưu unlimited track history
- Kết quả: RAM tăng liên tục

✅ **Đúng**: Limit history length hoặc cleanup old tracks

### 6. Thread safety issues
❌ **Sai**: Multiple threads access tracker không lock
- Kết quả: Race conditions, corrupt state

✅ **Đúng**: Use locks hoặc separate tracker per thread

---

## 📝 Configuration Checklist

### Tracker Parameters
- [ ] `iou_threshold` = 0.3 (vehicles move predictably)
- [ ] `max_age` = 30 (keep track 30 frames without detection)
- [ ] `min_hits` = 3 (confirm track sau 3 consecutive detections)
- [ ] `max_distance` = 0.7 (feature distance threshold)

### Vehicle Type Specific
- [ ] Car: Standard settings
- [ ] Motorcycle: Lower IOU (smaller, faster)
- [ ] Truck: Higher max_age (slower, stable)
- [ ] Bus: Higher max_age (large, stable)

### ROI Settings
- [ ] Entry/exit zones defined
- [ ] Direction vectors configured
- [ ] Violation zones marked
- [ ] Counting lines set

---

## 🔧 Implementation Checklist

### 1. Tracker Class
- [ ] Initialize DeepSORT tracker
- [ ] Implement update() method
- [ ] Implement predict() method
- [ ] Handle track lifecycle
- [ ] Store track metadata

### 2. ROI Integration
- [ ] Check if track enters ROI
- [ ] Check if track exits ROI
- [ ] Calculate dwell time
- [ ] Track direction of movement
- [ ] Log events

### 3. Violation Detection
- [ ] Stop line crossing detection
- [ ] Red light running detection
- [ ] Wrong direction detection
- [ ] Speed estimation (optional)
- [ ] No helmet detection (motorcycles)

### 4. Optimization
- [ ] Process every N frames (frame skip)
- [ ] Use lightweight features
- [ ] Batch processing
- [ ] GPU acceleration (nếu có)

---

## 📊 Tracking Metrics

### Accuracy Metrics
- **MOTA** (Multiple Object Tracking Accuracy)
- **MOTP** (Multiple Object Tracking Precision)
- **ID Switches**: Số lần ID bị đổi
- **Fragmentation**: Track bị đứt đoạn

### Performance Metrics
- **Processing Time**: ms per frame
- **Throughput**: FPS
- **Memory Usage**: RAM per camera
- **Active Tracks**: Số tracks đang active

### Quality Indicators
- **Average Track Length**: Frames per track
- **Track Confidence**: Confidence scores
- **Lost Tracks Rate**: % tracks lost
- **False Positives**: Tracks không phải xe

---

## 🧪 Testing Checklist

### Functional Tests
- [ ] Track xe qua nhiều frames
- [ ] IDs persistent qua occlusions
- [ ] Detect entry/exit ROI correctly
- [ ] Handle multiple vehicles
- [ ] Handle fast moving vehicles

### Edge Cases
- [ ] Xe bị che khuất hoàn toàn
- [ ] Xe đi vào/ra frame
- [ ] Xe đứng yên lâu
- [ ] Nhiều xe chồng lấn
- [ ] Lighting changes (ngày/đêm)

### Performance Tests
- [ ] Track 10+ vehicles simultaneously
- [ ] Maintain 15+ FPS
- [ ] Memory stable over time
- [ ] No memory leaks

---

## 🐛 Debugging Checklist

### ID Switches
- [ ] Visualize bboxes và IDs
- [ ] Check IOU thresholds
- [ ] Review matching algorithm
- [ ] Check appearance features

### Lost Tracks
- [ ] Check max_age setting
- [ ] Verify detection quality
- [ ] Check occlusion handling
- [ ] Review track deletion logic

### Performance Issues
- [ ] Profile tracking code
- [ ] Check feature extraction time
- [ ] Optimize matching algorithm
- [ ] Reduce number of tracks

---

## 📝 Usage Examples

### Example 1: Basic Tracking
**Input**:
- Detections: [[100,100,200,200], [300,100,400,200]]
- Confidences: [0.9, 0.85]
- Classes: [2, 2] (car)

**Processing**:
1. Match với existing tracks
2. No matches → Create 2 new tracks (ID: 1, 2)

**Output**:
```
Tracked objects:
- ID: 1, bbox: [100,100,200,200], class: car, age: 1
- ID: 2, bbox: [300,100,400,200], class: car, age: 1
```

### Example 2: ROI Entry Detection
**Scenario**: Xe vào vùng cấm

**Input**:
- Track ID 5 position: [150, 200]
- ROI polygon: [[100,100], [200,100], [200,300], [100,300]]

**Processing**:
1. Check point in polygon
2. Previous frame: outside
3. Current frame: inside
4. Event: Entry detected

**Output**:
```
ROI Entry Event:
- Track ID: 5
- ROI: "No Entry Zone"
- Timestamp: 2025-10-28 15:30:45
- Action: Create violation
```

### Example 3: Stop Line Violation
**Scenario**: Xe vượt vạch dừng khi đèn đỏ

**Input**:
- Track trajectory: [(100,150), (105,155), (110,160)]
- Stop line: y=165
- Traffic light: RED

**Processing**:
1. Check trajectory crosses stop line
2. Check traffic light status
3. Violation: Crossed on RED

**Output**:
```
Violation Detected:
- Type: red_light
- Track ID: 3
- Vehicle: car
- Plate: 29A-12345
- Evidence: Frame #1234
```

---

## 🔗 Related Prompts

- `detection/yolo.prompt.md` - Detections feed vào tracker
- `detection/violations.prompt.md` - Use tracking data
- `api/violations.prompt.md` - Store tracked violations
- `workflows/bug-fix.prompt.md` - Debug tracking issues
