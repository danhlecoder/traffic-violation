# Traffic Violation Detection - Backend

Backend API cho hệ thống phát hiện vi phạm giao thông sử dụng YOLO + ByteTrack.

## 📁 Cấu trúc thư mục

```
backend/
├── api/                        # REST API endpoints
│   ├── cameras.py             # Camera CRUD operations
│   ├── density.py             # Vehicle density metrics
│   ├── detection.py           # Stopline detection API
│   ├── lifecycle.py           # App startup/shutdown handlers
│   ├── middleware.py          # CORS middleware
│   ├── streams.py             # MJPEG streaming endpoint
│   └── violations.py          # Violations query & statistics
├── app.py                     # FastAPI application entry point
├── config/                    # Configuration
│   ├── config.py             # Settings (env vars, YAML)
│   ├── constants.py          # YOLO class colors, constants
│   └── server.yaml           # Server configuration
├── core/                      # Core business logic
│   ├── analysis/             # Image & traffic analysis
│   │   ├── density.py        # Vehicle counting & density
│   │   └── stopline.py       # Stopline detection (CV)
│   ├── detection/            # Object detection
│   │   ├── filters.py        # ROI filtering logic
│   │   └── yolo.py           # YOLO detector (singleton)
│   ├── streaming/            # Video streaming
│   │   ├── capture.py        # VideoCapture utilities
│   │   └── mjpeg.py          # MJPEG generator with detection
│   ├── tracking/             # Multi-object tracking
│   │   ├── roi_entry_tracker.py       # ROI state management
│   │   ├── stopline_tracker.py        # Stopline crossing detection
│   │   └── vehicle_tracker.py         # ByteTrack wrapper
│   └── violations/           # Violation management
│       ├── creator.py        # Create violation records
│       └── repository.py     # Save violations to MongoDB
├── models/                    # YOLO model weights
│   └── best1.pt              # Trained YOLOv8 model
├── schemas/                   # Data models
│   ├── camera.py             # Camera & CameraRegion schema
│   └── violation.py          # Violation schema
└── utils/                     # Shared utilities
    ├── database.py           # MongoDB connection & indexes
    ├── image.py              # Image processing helpers
    └── logger.py             # Logging configuration
```

## 🚀 Cài đặt

### 1. Dependencies
```bash
pip install -r requirements.txt
```

### 2. Cấu hình
Tạo file `.env`:
```bash
MONGO_HOST=mongo
MONGO_PORT=27017
YOLO_MODEL_PATH=/app/backend/models/best1.pt
YOLO_DEVICE=cpu
```

### 3. Chạy server
```bash
docker compose up -d
# hoặc
uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

## 📡 API Endpoints

### Cameras
- `GET /api/cameras` - Danh sách cameras
- `POST /api/cameras` - Thêm camera mới
- `PUT /api/cameras/{id}/regions` - Cập nhật ROI/stopline
- `DELETE /api/cameras/{id}` - Xóa camera

### Streaming
- `GET /api/stream?src={url}&fps=30&detection=true`
  - MJPEG stream với YOLO detection realtime
  - Tự động detect violations (ROI entry, stopline crossing)

### Violations
- `GET /api/violations` - Lấy danh sách violations (filter by camera, date, type)
- `GET /api/violations/stats` - Thống kê violations

### Detection
- `POST /api/detect/stopline` - Detect stopline từ ảnh base64

## 🤖 YOLO Classes

10 classes được detect:
1. bus, car, truck (vehicles)
2. motorcycle (vehicle 2 bánh)
3. helmet, no_helmet (vi phạm mũ bảo hiểm)
4. license_plate (biển số)
5. light_red, light_green, light_yellow (traffic lights)

## 🔧 Tech Stack

- **FastAPI** - REST API framework
- **Ultralytics YOLOv8** - Object detection
- **ByteTrack** - Multi-object tracking
- **OpenCV** - Image/video processing
- **MongoDB** - Database
- **Python 3.11** - Language

## 📝 Development

### Code Style
- Type hints required
- Docstrings in Vietnamese
- PEP8 compliant

### Testing
```bash
docker compose logs backend --tail 50
curl http://localhost:8000/api/health
```
