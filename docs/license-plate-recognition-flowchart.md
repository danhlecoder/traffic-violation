# Sơ Đồ Luồng Nhận Dạng Biển Số Xe

## 🎯 Tổng Quan Hệ Thống

Hệ thống nhận dạng biển số được tích hợp chặt chẽ với module theo dõi phương tiện (tracking), đảm bảo mỗi xe được gán một ID duy nhất và biển số tương ứng.

---

## 📊 Sơ Đồ Luồng Chính - Flowchart Truyền Thống

```
                                    ╭─────────────────────────╮
                                    │   START: Video Stream   │
                                    ╰───────────┬─────────────╯
                                                │
                                                ↓
                                    ┌───────────────────────────┐
                                    │  Capture Frame từ Video   │
                                    │   (OpenCV VideoCapture)   │
                                    ╰───────────┬───────────────╯
                                                │
                                                ↓
                                    ╭───────────────────────────╮
                                    │  Validate Frame hợp lệ?   │
                                    │   - Kiểm tra kích thước   │
                                    │   - Kiểm tra pixel values │
                                    ╰───────┬───────────┬───────╯
                                            │           │
                                        Có  │           │  Không
                                            ↓           ↓
                            ┌───────────────────────────┐  ←─────────┐
                            │ Chuẩn bị Frame            │             │
                            │ - Resize nếu cần          │             │
                            │ - Scale về detection size │             │
                            ╰───────────┬───────────────╯             │
                                        │                             │
                                        ↓                             │
                        ┌───────────────────────────────────────────┐
                        │      YOLO Detection Model                 │
                        │   Phát hiện đồng thời:                    │
                        │   • Vehicles: car, motorcycle, bus, truck │
                        │   • License Plates: license_plate         │
                        │   Output: bbox, confidence, class_name    │
                        ╰───────────┬───────────────────────────────╯
                                    │
                                    ↓
                        ┌───────────────────────────┐
                        │   Phân tách Objects       │
                        │   Vehicles ↔ Plates       │
                        ╰───────┬───────────┬───────╯
                                │           │
                    ┌───────────┘           └───────────┐
                    │                                   │
                    ↓                                   ↓
    ┌───────────────────────────────┐   ┌───────────────────────────────┐
    │   Vehicles                    │   │   License Plates              │
    │   (bbox, confidence, class)   │   │   (bbox, confidence)          │
    ╰───────────┬───────────────────╯   ╰───────────┬───────────────────╯
                │                                   │
                ↓                                   │
    ┌───────────────────────────────┐               │
    │   ByteTrack Object Tracker    │               │
    │   • IoU Matching              │               │
    │   • Center Distance           │               │
    │   • Track qua nhiều frames    │               │
    ╰───────────┬───────────────────╯               │
                │                                   │
                ↓                                   │
    ┌───────────────────────────────┐               │
    │   Gán Track ID duy nhất       │               │
    │   Format: 3 alphanumeric +    │               │
    │           HHMMSS              │               │
    │   Ví dụ: "2h6005200"          │               │
    ╰───────────┬───────────────────╯               │
                │                                   │
                ↓                                   ↓
    ┌───────────────────────────────┐   ╭───────────────────────────╮
    │   Tracked Vehicles            │   │ Biển số nằm trong vùng    │
    │   (bbox, track_id, class_name)│   │          xe nào?           │
    ╰───────────┬───────────────────╯   ╰───────┬───────────┬───────╯
                │                               │           │
                │                      Tìm thấy │           │ Không tìm thấy
                │                               ↓           ↓
                │              ┌───────────────────────────┐
                │              │ Match Plate với Vehicle   │
                │              │    theo IoU overlap       │
                │              ╰───────────┬───────────────╯
                │                          │
                │                          ↓
                │              ┌───────────────────────────┐
                │              │  Crop Plate từ Frame gốc  │
                │              ╰───────────┬───────────────╯
                │                          │
                └──────────────────────────┼──────────────────────────┐
                                           │                          │
                                           ↓                          ↓
                          ┌───────────────────────────┐   ┌───────────────────────────┐
                          │   Plate Crop 1 (Direct)   │   │  FALLBACK: Cắt vùng xe    │
                          │   từ Frame gốc            │   │  từ Frame gốc             │
                          ╰───────────┬───────────────╯   ╰───────────┬───────────────╯
                                      │                               │
                                      │                               ↓
                                      │               ┌───────────────────────────┐
                                      │               │  Chạy YOLO lại trên       │
                                      │               │  vùng xe đã cắt            │
                                      │               ╰───────────┬───────────────╯
                                      │                           │
                                      │                           ↓
                                      │               ╭───────────────────────────╮
                                      │               │ Phát hiện được plate      │
                                      │               │      trong crop?           │
                                      │               ╰───────┬───────────┬───────╯
                                      │                       │           │
                                      │                   Có  │           │  Không
                                      │                       ↓           ↓
                                      │       ┌───────────────────────────┐
                                      │       │  Crop Plate từ Vehicle    │
                                      │       │        Crop                │
                                      │       ╰───────────┬───────────────╯
                                      │                   │
                                      └───────────────────┼───────────────────────┐
                                                          │                       │
                                                          ↓                       ↓
                                    ┌───────────────────────────────────────────────────────┐
                                    │        PREPROCESSING PIPELINE                         │
                                    │  1. Resize nếu cần (max_edge=1600)                    │
                                    │  2. Deskew: Perspective Transform                     │
                                    │  3. CLAHE: Cân bằng histogram                        │
                                    │  4. Denoise: Bilateral Filter                        │
                                    │  5. Sharpen: Unsharp Masking                         │
                                    ╰───────────────────┬───────────────────────────────────╯
                                                        │
                                                        ↓
                                    ┌───────────────────────────────────────────┐
                                    │   YOLO Character Detection Model          │
                                    │   Phát hiện từng ký tự trên biển số       │
                                    │   ALLOWED_CHARS: 0-9, A-Z (không dấu)     │
                                    │   Không có: I, O, Q, R, W, J              │
                                    ╰───────────────────┬───────────────────────╯
                                                        │
                                                        ↓
                                    ┌───────────────────────────────────────────┐
                                    │   Sort Characters theo 2 hàng             │
                                    │   • Nhóm theo tọa độ Y                    │
                                    │   • Sort mỗi hàng theo tọa độ X           │
                                    │   • Dùng sort_boxes_two_rows()            │
                                    ╰───────────────────┬───────────────────────╯
                                                        │
                                                        ↓
                                    ┌───────────────────────────────────────────┐
                                    │   Ghép Text: Hàng 1 + "-" + Hàng 2        │
                                    │   Ví dụ: "30A-12345"                      │
                                    ╰───────────────────┬───────────────────────╯
                                                        │
                                                        ↓
                                    ┌───────────────────────────────────────────┐
                                    │           Plate Text OCR Result           │
                                    │         (Ví dụ: "30A-12345")             │
                                    ╰───────────────────┬───────────────────────╯
                                                        │
                ┌───────────────────────────────────────┼───────────────────────┐
                │                                       │                       │
                ↓                                       ↓                       ↓
    ┌───────────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────────┐
    │   Tracked Vehicles        │   │   Plate Text OCR          │   │   No Plate (None)        │
    │   (track_id, bbox, class) │   │   (e.g. "30A-12345")      │   │                          │
    ╰───────────┬───────────────╯   ╰───────────┬───────────────╯   ╰───────────┬───────────────╯
                │                               │                               │
                └───────────────────────────────┼───────────────────────────────┘
                                                │
                                                ↓
                                ┌───────────────────────────────────────────┐
                                │   Tạo Bản Ghi Vi Phạm                    │
                                │   • Track ID                             │
                                │   • Vehicle bbox + crop image            │
                                │   • Plate text OCR                       │
                                │   • Plate crop image                     │
                                │   • Timestamp (ISO format)               │
                                │   • Camera ID, Camera Name               │
                                │   • Violation Type                       │
                                ╰───────────────────┬───────────────────────╯
                                                    │
                                                    ↓
                                ┌───────────────────────────────────────────┐
                                │   Encode Bằng Chứng Base64               │
                                │   • overview_img (frame gốc + bbox)      │
                                │   • vehicle_img (crop xe)                 │
                                │   • plate_img (crop biển số)             │
                                │   • license_plate (text)                 │
                                ╰───────────────────┬───────────────────────╯
                                                    │
                                                    ↓
                                ╭───────────────────────────────╮
                                │                               │
                                │     MongoDB Storage           │
                                │                               │
                                ╰───────────────┬───────────────╯
                                                │
                                                ↓
                                    ╭───────────────────────────╮
                                    │         END               │
                                    ╰───────────────────────────╯

KÝ HIỆU:
╭───╮  ╰───╯   = Start/Stop (Oval)
┌───┐  └───┘   = Process Step (Rectangle)
╭───╮  ╰───╯   = Decision (Diamond)
╭───╮          = Disk Storage (Cylinder)
╰───╯
```

## 📊 Sơ Đồ Tổng Quan Ngắn Gọn

```
Video Stream
     ↓
┌──────────────────┐
│ YOLO Detection   │  → Phát hiện Vehicles + Plates đồng thời
└────────┬─────────┘
         │
         ├──→ Vehicles ──→ ByteTrack ──→ Track ID
         │
         └──→ Plates ──→ Check Overlap ──→ [Direct] hoặc [Fallback]
                            │                    │            │
                            │                    ↓            ↓
                            │              Crop từ frame  YOLO on crop
                            │                    │            │
                            └────────────────────┴────────────┘
                                                 ↓
                                         ┌───────────────┐
                                         │ Preprocessing │  (5 steps)
                                         └───────┬───────┘
                                                 ↓
                                         ┌───────────────┐
                                         │ YOLO Character│  OCR Model
                                         └───────┬───────┘
                                                 ↓
                                         ┌───────────────┐
                                         │ Sort & Combine│  Text
                                         └───────┬───────┘
                                                 ↓
                                         ┌───────────────┐
                                         │ Violation     │  Record
                                         │ + Evidence    │
                                         └───────┬───────┘
                                                 ↓
                                          ╭───────────╮
                                          │  MongoDB  │
                                          ╰───────────╯
```

---

## 🔍 Chi Tiết Từng Bước

### 1. **Video Stream & Frame Capture**
- **Input**: RTSP/USB video stream
- **File**: `backend/core/streaming/mjpeg.py`
- **Xử lý**:
  - Capture frame từ OpenCV VideoCapture
  - Validate frame (kiểm tra kích thước, pixel values)
  - Resize frame nếu cần để tối ưu detection

### 2. **YOLO Detection - Phát Hiện Đồng Thời**
- **Model**: YOLOv8/v11 Detection Model
- **File**: `backend/core/detection/yolo.py`
- **Classes phát hiện**:
  - Vehicles: `car`, `motorcycle`, `bus`, `truck`
  - License Plates: `license_plate`
- **Output**: List detections với `bbox`, `confidence`, `class_name`

### 3. **Object Tracking - Gán Track ID**
- **Algorithm**: ByteTrack (IoU-based matching)
- **File**: `backend/core/tracking/vehicle_tracker.py`
- **Chức năng**:
  - Gán ID duy nhất cho mỗi xe (format: `2h6005200` = 3 ký tự random + HHMMSS)
  - Theo dõi xe qua nhiều frames
  - Xử lý occlusion và re-identification
- **Config**:
  - `iou_threshold`: 0.3 (ngưỡng IoU để match)
  - `max_age`: 30 frames (giữ track lost tối đa)
  - `min_hits`: 3 (số hits tối thiểu để confirm track)

### 4. **License Plate Matching - Hai Chiến Lược**

#### **Chiến lược 1: Direct Detection** ✅
- Biển số được phát hiện trực tiếp từ YOLO detection
- Kiểm tra IoU overlap giữa plate và vehicle bbox
- Nếu plate nằm trong vùng xe → match và crop trực tiếp

#### **Chiến lược 2: Fallback Detection** 🔄
- **File**: `backend/core/violations/creator.py` (line 164-218)
- Khi không phát hiện được plate từ frame gốc:
  1. Crop vùng xe từ frame (với padding)
  2. Chạy YOLO detection lại trên vùng xe đã cắt
  3. Tìm `license_plate` trong crop detections
  4. Crop plate từ vehicle crop
- **Lợi ích**:
  - Thu hẹp bối cảnh → giảm nhiễu nền
  - Tăng khả năng phát hiện plate nhỏ/xa
  - Confidence threshold thấp hơn (0.2-0.3) để tăng recall

### 5. **Preprocessing Pipeline** 🎨
- **File**: `backend/core/license_plate/preprocessing.py`
- **Quy trình 5 bước**:

```python
# 1. Resize nếu cạnh dài > 1600px
bgr_resized = clip_long_edge(bgr, max_len=1600)

# 2. Deskew - Perspective Transform
bgr_rect = step2_rectify(bgr_resized)
# Tìm contour biển số, perspective transform về hình chữ nhật

# 3. CLAHE - Cân bằng histogram
gray = cv2.cvtColor(bgr_rect, cv2.COLOR_BGR2GRAY)
gray_eq = cv2.createCLAHE(clipLimit=3.0).apply(gray)

# 4. Denoise - Bilateral Filter
gray_dn = cv2.bilateralFilter(gray_eq, d=5, sigmaColor=60, sigmaSpace=60)

# 5. Sharpen - Unsharp Masking
blur = cv2.GaussianBlur(gray_dn, (0,0), 1.2)
gray_refined = cv2.addWeighted(gray_dn, 1.8, blur, -0.8, 0)
```

### 6. **YOLO Character Detection - OCR Model** 🔤
- **Model**: YOLOv8 Character Detection (riêng biệt)
- **File**: `backend/core/license_plate/detector.py`
- **ALLOWED_CHARS**:
  - Số: `0-9`
  - Chữ cái: `A, B, C, D, E, F, G, H, K, L, M, N, P, S, T, U, V, X, Y, Z`
  - *Không có*: I, O, Q, R, W, J (tránh nhầm lẫn)
- **Config**:
  - `conf_threshold`: 0.25 (từ settings.LP_CONF_THRESHOLD)
  - `iou_threshold`: 0.6
  - `device`: CUDA/CPU auto-detect

### 7. **Character Sorting - Sắp Xếp Ký Tự** 📋
- **Function**: `sort_boxes_two_rows(boxes_xyxy)`
- **File**: `backend/core/license_plate/preprocessing.py`
- **Algorithm**:
  1. Tính center (cx, cy) của mỗi bbox
  2. Tính median height để xác định row_threshold
  3. Nhóm ký tự thành 2 hàng dựa trên tọa độ Y
  4. Sort mỗi hàng theo tọa độ X (trái → phải)
  5. Ghép text: `Hàng1 + "-" + Hàng2`

**Ví dụ**:
```
Hàng 1: [3, 0, A]        → "30A"
Hàng 2: [1, 2, 3, 4, 5]  → "12345"
Result: "30A-12345"
```

### 8. **Violation Record Creation** 💾
- **File**: `backend/core/violations/creator.py`
- **Dữ liệu lưu trữ**:
```python
{
    "timestamp": "2025-11-23T14:30:45",
    "camera_id": "cam_001",
    "track_id": "2h6005200",
    "vehicle_type": "motorcycle",
    "license_plate": "30A-12345",  # OCR result
    "images": {
        "overview_img": "base64...",   # Frame gốc có vẽ bbox
        "vehicle_img": "base64...",    # Crop xe
        "plate_img": "base64..."       # Crop biển số
    },
    "violation_type": "red_light",
    "confidence": 0.85
}
```

---

## 🔧 Các Model Sử Dụng

| Model | Mục đích | Config File | Device |
|-------|----------|-------------|---------|
| YOLO Detection | Phát hiện vehicles + plates | `YOLO_MODEL_PATH` | GPU/CPU auto |
| YOLO Character OCR | Nhận dạng ký tự biển số | `LP_MODEL_PATH` | GPU/CPU auto |

**Config trong `backend/config/server.yaml`**:
```yaml
yolo:
  model_path: "./models/yolov8n.pt"
  device: "cuda"  # auto, cuda, cpu
  conf_default: 0.4
  iou_default: 0.5

license_plate:
  model_path: "./models/license_plate_ocr.pt"
  device: "cuda"
  conf_threshold: 0.25
```

---

## 📈 Luồng Dữ Liệu Tổng Quát

```
Video Stream
    ↓
YOLO Detection (Vehicles + Plates)
    ↓
ByteTrack (Track ID Assignment)
    ↓
┌─────────────────────────────────┐
│ Plate Detection Strategy        │
│ 1. Direct: từ frame gốc        │
│ 2. Fallback: từ vehicle crop  │
└─────────────────────────────────┘
    ↓
Preprocessing (5 steps)
    ↓
YOLO Character Detection
    ↓
Sort & Combine Text
    ↓
Violation Record + Evidence
    ↓
MongoDB Storage
```

---

## 🎯 Ưu Điểm Kiến Trúc

1. **Two-Stage Detection**
   - Phát hiện plate trực tiếp (fast, high precision)
   - Fallback detection trên crop (high recall)

2. **Preprocessing Pipeline**
   - Deskew: Xử lý biển số nghiêng
   - CLAHE: Tăng contrast ký tự
   - Denoise + Sharpen: Giảm nhiễu, tăng độ sắc nét

3. **YOLO-based OCR**
   - Không phụ thuộc Tesseract OCR
   - Huấn luyện riêng cho biển số Việt Nam
   - Detection-based → chính xác cao hơn

4. **Integrated Tracking**
   - Gắn biển số với Track ID ổn định
   - Theo dõi xe qua nhiều frames
   - Tránh duplicate violations

---

## 📚 Files Liên Quan

### Core Detection
- `backend/core/detection/yolo.py` - YOLO detector wrapper
- `backend/core/tracking/vehicle_tracker.py` - ByteTrack implementation

### License Plate
- `backend/core/license_plate/detector.py` - OCR model
- `backend/core/license_plate/preprocessing.py` - Preprocessing pipeline

### Violation Processing
- `backend/core/violations/creator.py` - Tạo violation record
- `backend/core/streaming/mjpeg.py` - Video processing loop

### Config
- `backend/config/config.py` - Settings loader
- `backend/config/server.yaml` - YAML configuration

---

## 🚀 Tối Ưu Hóa

### Hiện tại
- ✅ GPU acceleration (CUDA + half precision)
- ✅ Frame skipping (configurable)
- ✅ Confidence threshold tuning
- ✅ Two-stage detection strategy

### Có thể cải thiện
- 🔄 Batch processing cho multiple vehicles
- 🔄 Caching OCR results theo track_id
- 🔄 Async processing pipeline
- 🔄 Model quantization (INT8) cho edge devices

---

**Ngày tạo**: 23/11/2025
**Phiên bản**: 1.0
**Tác giả**: AI Assistant (Cursor AI)

