# Traffic Violation Detection - Backend

Backend API cho hệ thống phát hiện vi phạm giao thông sử dụng YOLO.

## 📁 Cấu trúc thư mục

```
backend/
├── app.py                      # Entry point - FastAPI application
├── core/                       # Cấu hình và hằng số
│   ├── __init__.py
│   ├── config.py              # Settings và environment variables
│   └── constants.py           # Hằng số (classes, colors, etc.)
├── schemas/                   # Pydantic models cho validation
│   ├── __init__.py
│   └── camera.py             # Schema cho Camera, Region
├── models/                    # AI Models và Detection
│   ├── __init__.py
│   └── yolo_detector.py      # YOLO detection service
├── routers/                   # API endpoints
│   ├── __init__.py
│   ├── cameras.py            # Camera management API
│   └── streams.py            # Streaming và detection API
├── src/
│   ├── rtsp_stream/          # RTSP/MJPEG streaming
│   │   ├── __init__.py
│   │   └── streamer.py
│   ├── services/             # Business logic services
│   │   ├── __init__.py
│   │   └── db.py            # MongoDB service
│   └── utils/                # Utilities
│       ├── __init__.py
│       ├── logger.py         # Logging configuration
│       └── detec_line.py     # Stop line detection
├── model/                     # YOLO model files
│   └── best.pt               # YOLOv8 trained model
└── configs/
    └── server.yaml           # YAML config (fallback)
```

## 🚀 Cài đặt và Chạy

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Cấu hình

Copy file `.env.example` thành `.env` và chỉnh sửa:

```bash
cp ../.env.example .env
```

Các cấu hình quan trọng:
- `YOLO_MODEL_PATH`: Đường dẫn tới file model YOLO (.pt)
- `MONGO_HOST`, `MONGO_PORT`: Thông tin MongoDB
- `YOLO_DEVICE`: `cpu` hoặc `cuda` (nếu có GPU)

### 3. Chạy server

```bash
# Chạy với uvicorn
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload

# Hoặc chạy trực tiếp
python -m backend.app
```

### 4. Kiểm tra health

```bash
curl http://localhost:8000/api/health
```

## 📡 API Endpoints

### Cameras Management

- `GET /api/cameras` - Lấy danh sách cameras
- `POST /api/cameras` - Thêm/cập nhật camera
- `GET /api/cameras/{cam_id}` - Lấy thông tin camera
- `PUT /api/cameras/{cam_id}/regions` - Cập nhật regions (ROI, stopline)
- `DELETE /api/cameras/{cam_id}` - Xóa camera

### Streaming

- `GET /api/stream?src={rtsp_url}&fps={fps}&quality={quality}&detection={true/false}`
  - Stream MJPEG với YOLO detection
  - Tham số:
    - `src`: URL RTSP/HTTP (bắt buộc)
    - `fps`: Frame per second (1-60, mặc định: 30)
    - `quality`: Chất lượng JPEG (10-95, mặc định: 80)
    - `detection`: Bật/tắt detection (mặc định: true)

### Detection

- `POST /api/detect/stopline` - Phát hiện vạch dừng từ ảnh base64

## 🤖 YOLO Detection

### Classes được hỗ trợ

Model YOLO được train để phát hiện 10 classes:

1. `bus` - Xe buýt
2. `car` - Ô tô
3. `helmet` - Mũ bảo hiểm
4. `license_plate` - Biển số xe
5. `light_green` - Đèn xanh
6. `light_red` - Đèn đỏ
7. `light_yellow` - Đèn vàng
8. `motorcycle` - Xe máy
9. `no_helmet` - Không mũ bảo hiểm
10. `truck` - Xe tải

### Cấu hình Detection

Trong file `.env`:

```bash
# Confidence threshold (càng cao càng chính xác nhưng ít detection hơn)
YOLO_CONFIDENCE=0.25

# IOU threshold cho Non-Maximum Suppression
YOLO_IOU_THRESHOLD=0.45

# Device
YOLO_DEVICE=cpu  # hoặc cuda nếu có GPU
```

### Sử dụng trong code

```python
from backend.models.yolo_detector import get_yolo_detector

# Lấy detector instance (singleton)
detector = get_yolo_detector()

# Detect objects
detections = detector.detect(frame)

# Detect và vẽ bounding boxes
annotated_frame, detections = detector.detect_and_draw(frame)
```

## 🗄️ Database

Sử dụng MongoDB để lưu trữ:
- Thông tin cameras
- Regions (ROI, stop line)
- Violations (tương lai)

### Collections

- `cameras`: Lưu thông tin camera và regions

## 📝 Logging

Logs được lưu tại: `/app/logs/backend.log` (hoặc theo `LOG_FILE` trong .env)

3 logger chính:
- `traffic.app` - Application logs
- `traffic.stream` - Streaming logs
- `traffic.detector` - Detection logs

## 🔧 Development

### Code Style

- Tuân theo PEP8
- Sử dụng type hints
- Comment và docstring bằng tiếng Việt
- Tổ chức code theo module rõ ràng

### Thêm module mới

1. Tạo file trong thư mục tương ứng
2. Export trong `__init__.py`
3. Import và sử dụng

### Testing

```bash
# Chạy tests (TODO)
pytest tests/
```

## 🐛 Troubleshooting

### Lỗi "Model file not found"
- Kiểm tra `YOLO_MODEL_PATH` trong `.env`
- Đảm bảo file `best.pt` tồn tại

### Lỗi "Cannot import ultralytics"
```bash
pip install ultralytics
```

### Lỗi MongoDB connection
- Kiểm tra MongoDB đang chạy
- Kiểm tra `MONGO_HOST` và `MONGO_PORT`

### Stream không có detection
- Kiểm tra `detection=true` trong URL
- Xem logs để biết lỗi chi tiết
- Kiểm tra model đã load thành công chưa

## 📚 Tài liệu tham khảo

- [FastAPI](https://fastapi.tiangolo.com/)
- [Ultralytics YOLO](https://docs.ultralytics.com/)
- [MongoDB](https://www.mongodb.com/docs/)
- [OpenCV](https://docs.opencv.org/)



