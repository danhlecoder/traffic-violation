# 🚀 YOLO DETECTION - PROMPT

## 📋 Metadata
```yaml
tags: [detection, yolo, object-detection, computer-vision]
inputs:
  - frame (numpy array hoặc image path)
  - confidence_threshold (float)
  - classes (list of vehicle types)
tools:
  - YOLOv8 (ultralytics)
  - OpenCV
  - torch/CUDA
output_format: Detections với bboxes, confidence, classes
complexity: High
```

---

## 🎯 Chức năng

### Module: YOLO Vehicle Detector
**Mục đích**: Detect vehicles trong video frames

**Vị trí file**: `backend/core/detection/yolo.py`

**Models hỗ trợ**: YOLOv8n, YOLOv8s, YOLOv8m, YOLOv8l

**Vehicle Classes**:
- Car (class 2)
- Motorcycle (class 3)
- Bus (class 5)
- Truck (class 7)

**Pipeline**:
1. Load YOLO model (1 lần khi init)
2. Nhận frame từ camera
3. Preprocess frame
4. Run inference
5. Post-process results (NMS)
6. Filter theo confidence và classes
7. Return detections

---

## ✅ Checklist Detection Flow

### 1. Model Loading
- [ ] Choose model size (n/s/m/l based on GPU)
- [ ] Load pretrained weights
- [ ] Set device (cuda/cpu)
- [ ] Configure model parameters
- [ ] Warm up model (dummy inference)

### 2. Preprocessing
- [ ] Resize frame về input size (640x640 default)
- [ ] Normalize pixel values
- [ ] Convert BGR → RGB (nếu dùng OpenCV)
- [ ] Batch frames (nếu có nhiều cameras)

### 3. Inference
- [ ] Forward pass qua model
- [ ] Handle GPU memory
- [ ] Batch processing (nếu có)
- [ ] Measure inference time

### 4. Post-processing
- [ ] Non-Maximum Suppression (NMS)
- [ ] Filter theo confidence threshold
- [ ] Filter theo class IDs
- [ ] Convert coordinates về original size
- [ ] Sort theo confidence

### 5. Result Formatting
- [ ] Extract bboxes [x1,y1,x2,y2]
- [ ] Extract confidences
- [ ] Extract class IDs
- [ ] Map class IDs → class names
- [ ] Return structured results

---

## ⚠️ Pitfalls - Lỗi thường gặp

### 1. Model không cache
❌ **Sai**: Load model mỗi lần detect
- Kết quả: Startup time 5-10s mỗi frame

✅ **Đúng**: Load 1 lần khi init, reuse

### 2. Confidence threshold không phù hợp
❌ **Sai**: threshold=0.9 → Miss nhiều vehicles
❌ **Sai**: threshold=0.1 → Quá nhiều false positives

✅ **Đúng**: threshold=0.5-0.6 cho vehicles

### 3. Không dùng GPU
❌ **Sai**: Force CPU khi có GPU
- Kết quả: 10x chậm hơn

✅ **Đúng**: Auto detect GPU, fallback CPU

### 4. Process full resolution
❌ **Sai**: Inference trên 4K frames
- Kết quả: Rất chậm, OOM errors

✅ **Đúng**: Resize về 640x640 hoặc 1280x1280

### 5. Không skip frames
❌ **Sai**: Process mọi frame 30fps
- Kết quả: Waste resources, không cần thiết

✅ **Đúng**: Process every 2-3 frames (10-15fps đủ)

### 6. NMS threshold không đúng
❌ **Sai**: NMS threshold quá thấp
- Kết quả: Duplicate detections

✅ **Đúng**: NMS IOU threshold 0.4-0.5

### 7. Memory leaks
❌ **Sai**: Không clear GPU cache
- Kết quả: OOM sau vài giờ

✅ **Đúng**: `torch.cuda.empty_cache()` periodically

---

## 📝 Configuration Checklist

### Model Selection
- [ ] **YOLOv8n**: Fastest, accuracy thấp nhất (good for CPU)
- [ ] **YOLOv8s**: Balanced (recommended)
- [ ] **YOLOv8m**: Better accuracy, slower
- [ ] **YOLOv8l**: Best accuracy, slowest (need good GPU)

### Thresholds
- [ ] `conf_threshold` = 0.5 (vehicle detection)
- [ ] `iou_threshold` = 0.45 (NMS)
- [ ] `max_det` = 100 (max detections per frame)

### Input Settings
- [ ] `imgsz` = 640 (hoặc 1280 nếu cần accuracy cao)
- [ ] `stride` = 32 (model stride)
- [ ] `half` = True (FP16 inference nếu GPU hỗ trợ)

### Performance
- [ ] `device` = 'cuda:0' hoặc 'cpu'
- [ ] `batch_size` = 1 (realtime) hoặc 4-8 (offline)
- [ ] `workers` = 4 (dataloader workers)

### Classes Filter
- [ ] Filter chỉ vehicle classes: [2, 3, 5, 7]
- [ ] Bỏ qua person, bicycle, etc (giảm false positives)

---

## 🔧 Implementation Checklist

### 1. Detector Class
- [ ] Initialize YOLO model trong __init__
- [ ] Implement detect() method
- [ ] Implement batch_detect() method (optional)
- [ ] Handle errors gracefully
- [ ] Log performance metrics

### 2. Frame Processing
- [ ] Accept numpy array hoặc PIL Image
- [ ] Handle different input formats
- [ ] Validate input shape
- [ ] Auto-resize if needed

### 3. Result Format
```python
{
  "detections": [
    {
      "bbox": [x1, y1, x2, y2],
      "confidence": 0.87,
      "class_id": 2,
      "class_name": "car"
    }
  ],
  "inference_time": 0.023,  # seconds
  "num_detections": 3
}
```

### 4. Optimization
- [ ] Use TensorRT (nếu NVIDIA GPU)
- [ ] Use ONNX export (faster inference)
- [ ] Batch inference (multiple cameras)
- [ ] Multi-threading cho preprocessing

---

## 📊 Performance Benchmarks

### GPU (NVIDIA RTX 3060)
| Model | Input Size | FPS | mAP |
|-------|------------|-----|-----|
| YOLOv8n | 640 | 120 | 0.37 |
| YOLOv8s | 640 | 80 | 0.44 |
| YOLOv8m | 640 | 45 | 0.50 |
| YOLOv8l | 640 | 25 | 0.52 |

### CPU (Intel i7)
| Model | Input Size | FPS | mAP |
|-------|------------|-----|-----|
| YOLOv8n | 640 | 15 | 0.37 |
| YOLOv8s | 640 | 8 | 0.44 |

**Recommendation**:
- GPU deployment: YOLOv8s hoặc YOLOv8m
- CPU deployment: YOLOv8n

---

## 🧪 Testing Checklist

### Functional Tests
- [ ] Detect cars correctly
- [ ] Detect motorcycles correctly
- [ ] Detect trucks/buses correctly
- [ ] Ignore non-vehicle objects
- [ ] Handle empty frames (no vehicles)

### Edge Cases
- [ ] Partial vehicles (frame edges)
- [ ] Occluded vehicles
- [ ] Night time / low light
- [ ] Rain / fog
- [ ] Multiple vehicles overlapping

### Performance Tests
- [ ] Inference time < 50ms per frame (GPU)
- [ ] Inference time < 200ms per frame (CPU)
- [ ] No memory leaks over 1000 frames
- [ ] GPU memory usage stable

### Accuracy Tests
- [ ] Precision > 85% (detected vehicles là xe thật)
- [ ] Recall > 80% (detect được 80% xe trong frame)
- [ ] False positives < 15%
- [ ] False negatives < 20%

---

## 🐛 Debugging Checklist

### Low Detection Rate
- [ ] Check confidence threshold (lower it)
- [ ] Check input image quality
- [ ] Verify model loaded correctly
- [ ] Check if correct classes filtered
- [ ] Try different model size

### False Positives
- [ ] Increase confidence threshold
- [ ] Adjust NMS threshold
- [ ] Filter non-vehicle classes
- [ ] Check training data quality

### Slow Performance
- [ ] Check GPU utilization (`nvidia-smi`)
- [ ] Reduce input size
- [ ] Use smaller model
- [ ] Enable FP16 inference
- [ ] Batch processing

### Memory Issues
- [ ] Clear GPU cache
- [ ] Reduce batch size
- [ ] Check for leaks
- [ ] Monitor with `nvidia-smi`

---

## 📝 Usage Examples

### Example 1: Single Frame Detection
**Input**:
- Frame: 1920x1080 image
- Confidence: 0.5
- Classes: [2, 3] (car, motorcycle)

**Processing**:
- Resize → 640x640
- Inference time: 28ms
- Detections found: 4

**Output**:
```
{
  "detections": [
    {"bbox": [120,300,450,580], "conf": 0.87, "class": "car"},
    {"bbox": [600,200,750,400], "conf": 0.92, "class": "car"},
    {"bbox": [800,150,900,350], "conf": 0.65, "class": "motorcycle"},
    {"bbox": [100,100,200,250], "conf": 0.58, "class": "motorcycle"}
  ],
  "inference_time": 0.028
}
```

### Example 2: Batch Processing
**Input**: 4 cameras, 4 frames simultaneously

**Processing**:
- Stack frames → batch of 4
- Single forward pass
- Split results

**Performance**: 4x faster than sequential

---

## 🔗 Related Prompts

- `detection/tracking.prompt.md` - Use YOLO detections
- `detection/license-plate.prompt.md` - OCR sau khi detect vehicle
- `detection/violations.prompt.md` - Violations từ detections
- `deployment/docker.prompt.md` - Deploy YOLO service
