# 🚀 Hướng dẫn Sử dụng - Traffic Violation Detection System

## 📋 Mục lục

1. [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
2. [Cài đặt](#cài-đặt)
3. [Cấu hình](#cấu-hình)
4. [Chạy ứng dụng](#chạy-ứng-dụng)
5. [Sử dụng API](#sử-dụng-api)
6. [Cấu hình YOLO](#cấu-hình-yolo)
7. [Troubleshooting](#troubleshooting)

---

## 🖥️ Yêu cầu hệ thống

### Phần cứng
- **CPU**: Intel i5 hoặc tương đương (khuyến nghị i7+)
- **RAM**: Tối thiểu 4GB (khuyến nghị 8GB+)
- **GPU**: Không bắt buộc (nếu có CUDA sẽ nhanh hơn)
- **Ổ cứng**: 5GB trống

### Phần mềm
- **Python**: 3.10 hoặc 3.11
- **Docker**: 20.10+ (nếu dùng Docker)
- **MongoDB**: 5.0+ (hoặc dùng Docker)
- **Git**: Để clone repository

---

## 📥 Cài đặt

### Cách 1: Sử dụng Docker (Khuyến nghị)

```bash
# 1. Clone repository
git clone <repository-url>
cd traffic-violation

# 2. Chạy Docker Compose
docker compose up -d --build

# 3. Kiểm tra
curl http://localhost:8000/api/health
```

**Xong!** Ứng dụng đã chạy:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- MongoDB: localhost:27017

### Cách 2: Cài đặt thủ công

#### Bước 1: Clone repository
```bash
git clone <repository-url>
cd traffic-violation
```

#### Bước 2: Cài đặt Python dependencies
```bash
# Tạo virtual environment (khuyến nghị)
python -m venv venv

# Kích hoạt virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Cài đặt packages
pip install -r requirements.txt
```

#### Bước 3: Cài đặt MongoDB

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install -y mongodb
sudo systemctl start mongodb
sudo systemctl enable mongodb
```

**macOS:**
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

**Windows:**
Tải và cài đặt từ: https://www.mongodb.com/try/download/community

#### Bước 4: Cấu hình
```bash
# Copy file .env mẫu
cp .env.example .env

# Chỉnh sửa file .env
nano .env  # hoặc dùng editor khác
```

---

## ⚙️ Cấu hình

### File `.env`

Tạo file `.env` trong thư mục gốc với nội dung:

```bash
# === SERVER ===
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=*

# === DATABASE ===
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DATABASE=traffic
MONGO_USERNAME=
MONGO_PASSWORD=

# === YOLO MODEL ===
# ⚠️ QUAN TRỌNG: Chỉ định đường dẫn tới model
YOLO_MODEL_PATH=./backend/model/best.pt

# Confidence threshold (0.0 - 1.0)
YOLO_CONFIDENCE=0.25

# IOU threshold
YOLO_IOU_THRESHOLD=0.45

# Device: cpu hoặc cuda
YOLO_DEVICE=cpu

# === STREAM ===
STREAM_DEFAULT_FPS=30
STREAM_DEFAULT_QUALITY=80
```

### Đặt file model YOLO

```bash
# Tạo thư mục model
mkdir -p backend/model

# Copy file best.pt vào thư mục
cp /path/to/your/best.pt backend/model/

# Kiểm tra
ls -lh backend/model/best.pt
```

---

## 🏃 Chạy ứng dụng

### Backend

```bash
# Cách 1: Uvicorn (development)
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload

# Cách 2: Python trực tiếp
python -m backend.app

# Cách 3: Docker
docker compose up backend
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Kiểm tra

```bash
# Backend health check
curl http://localhost:8000/api/health

# Expected output:
# {
#   "status": "ok",
#   "version": "1.0.0",
#   "yolo_model": "/app/backend/model/best.pt",
#   ...
# }
```

---

## 📡 Sử dụng API

### 1. Quản lý Cameras

#### Lấy danh sách cameras
```bash
curl http://localhost:8000/api/cameras
```

#### Thêm camera mới
```bash
curl -X POST http://localhost:8000/api/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "id": "cam001",
    "name": "Camera Ngã Tư ABC",
    "rtsp": "rtsp://camera.example.com/stream",
    "location": "Ngã tư ABC, Quận 1"
  }'
```

#### Cập nhật regions (vạch dừng, ROI)
```bash
curl -X PUT http://localhost:8000/api/cameras/cam001/regions \
  -H "Content-Type: application/json" \
  -d '{
    "stopLine": [
      {"x": 0.1, "y": 0.8},
      {"x": 0.9, "y": 0.8}
    ],
    "roi": [
      {"x": 0.0, "y": 0.5},
      {"x": 1.0, "y": 0.5},
      {"x": 1.0, "y": 1.0},
      {"x": 0.0, "y": 1.0}
    ]
  }'
```

### 2. Streaming với YOLO Detection

#### Stream với detection (mặc định)
```html
<!-- Trong HTML -->
<img src="http://localhost:8000/api/stream?src=rtsp://camera.com/stream" />
```

#### Stream với tham số tùy chỉnh
```
http://localhost:8000/api/stream?src=rtsp://camera.com/stream&fps=20&quality=70&detection=true
```

**Tham số:**
- `src`: URL RTSP/HTTP (bắt buộc, cần encode URL)
- `fps`: Frame per second (1-60, mặc định: 30)
- `quality`: Chất lượng JPEG (10-95, mặc định: 80)
- `detection`: Bật/tắt YOLO detection (true/false, mặc định: true)

#### Tắt detection (stream nhanh hơn)
```
http://localhost:8000/api/stream?src=rtsp://camera.com/stream&detection=false
```

### 3. Phát hiện vạch dừng từ ảnh

```bash
curl -X POST http://localhost:8000/api/detect/stopline \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/jpeg;base64,/9j/4AAQ..."
  }'
```

**Response:**
```json
{
  "stopLine": [
    {"x": 0.1, "y": 0.75},
    {"x": 0.9, "y": 0.78}
  ]
}
```

---

## 🤖 Cấu hình YOLO

### Classes được detect

Model detect 10 loại đối tượng:

| Class | Tên tiếng Việt | Mô tả |
|-------|---------------|-------|
| `bus` | Xe buýt | Xe buýt công cộng |
| `car` | Ô tô | Xe ô tô |
| `motorcycle` | Xe máy | Xe máy, xe gắn máy |
| `truck` | Xe tải | Xe tải các loại |
| `helmet` | Mũ bảo hiểm | Người đội mũ bảo hiểm |
| `no_helmet` | Không mũ | Người không đội mũ |
| `license_plate` | Biển số | Biển số xe |
| `light_red` | Đèn đỏ | Đèn giao thông đỏ |
| `light_yellow` | Đèn vàng | Đèn giao thông vàng |
| `light_green` | Đèn xanh | Đèn giao thông xanh |

### Điều chỉnh độ nhạy

Trong file `.env`:

```bash
# Confidence threshold
# - Cao hơn (0.5-0.9): Chính xác hơn, ít false positive, nhưng có thể bỏ sót
# - Thấp hơn (0.1-0.3): Detect nhiều hơn, nhưng có thể có false positive
YOLO_CONFIDENCE=0.25

# IOU threshold (Non-Maximum Suppression)
# - Cao hơn (0.6-0.9): Giữ nhiều boxes chồng lấp
# - Thấp hơn (0.3-0.5): Loại bỏ boxes trùng lặp mạnh hơn
YOLO_IOU_THRESHOLD=0.45
```

### Sử dụng GPU (nếu có)

```bash
# Kiểm tra CUDA có sẵn không
python -c "import torch; print(torch.cuda.is_available())"

# Nếu có CUDA, sửa .env:
YOLO_DEVICE=cuda

# Hoặc chỉ định GPU cụ thể:
YOLO_DEVICE=cuda:0
```

---

## 🔧 Troubleshooting

### Lỗi: "Model file not found"

**Nguyên nhân:** Không tìm thấy file model YOLO

**Giải pháp:**
```bash
# 1. Kiểm tra file tồn tại
ls -lh backend/model/best.pt

# 2. Kiểm tra đường dẫn trong .env
cat .env | grep YOLO_MODEL_PATH

# 3. Sửa đường dẫn cho đúng
# Nếu chạy trực tiếp:
YOLO_MODEL_PATH=./backend/model/best.pt

# Nếu chạy trong Docker:
YOLO_MODEL_PATH=/app/backend/model/best.pt
```

### Lỗi: "Cannot import ultralytics"

**Nguyên nhân:** Chưa cài đặt ultralytics

**Giải pháp:**
```bash
pip install ultralytics
```

### Lỗi MongoDB connection

**Nguyên nhân:** MongoDB không chạy hoặc cấu hình sai

**Giải pháp:**
```bash
# 1. Kiểm tra MongoDB đang chạy
sudo systemctl status mongodb
# hoặc
docker ps | grep mongo

# 2. Kiểm tra kết nối
mongosh --eval "db.version()"

# 3. Kiểm tra cấu hình .env
cat .env | grep MONGO
```

### Stream không hiển thị

**Nguyên nhân:** URL RTSP không hợp lệ hoặc camera offline

**Giải pháp:**
```bash
# 1. Test RTSP bằng ffmpeg
ffmpeg -i "rtsp://camera.com/stream" -frames:v 1 test.jpg

# 2. Test RTSP bằng VLC
vlc rtsp://camera.com/stream

# 3. Kiểm tra logs
tail -f logs/backend.log | grep stream
```

### Detection chậm

**Giải pháp:**

1. **Giảm FPS:**
   ```
   ?fps=15  # Thay vì 30
   ```

2. **Giảm Quality:**
   ```
   ?quality=60  # Thay vì 80
   ```

3. **Sử dụng GPU:**
   ```bash
   YOLO_DEVICE=cuda
   ```

4. **Tắt detection nếu không cần:**
   ```
   ?detection=false
   ```

### Out of Memory

**Giải pháp:**

1. **Giảm số lượng streams đồng thời**

2. **Giảm resolution** (trong camera settings)

3. **Tăng RAM** hoặc sử dụng swap

4. **Restart service** định kỳ

---

## 📊 Monitoring

### Kiểm tra logs

```bash
# Tất cả logs
tail -f logs/backend.log

# Chỉ errors
tail -f logs/backend.log | grep ERROR

# Chỉ detection logs
tail -f logs/backend.log | grep detector
```

### Kiểm tra health

```bash
# Script kiểm tra định kỳ
while true; do
  curl -s http://localhost:8000/api/health | jq .status
  sleep 10
done
```

### Monitor resources

```bash
# CPU, Memory
htop

# GPU (nếu có)
nvidia-smi -l 1

# Docker stats
docker stats
```

---

## 🎯 Best Practices

1. **Luôn sử dụng GPU nếu có** để tăng tốc độ detection
2. **Điều chỉnh confidence** phù hợp với từng camera
3. **Monitor logs** để phát hiện lỗi sớm
4. **Backup database** định kỳ
5. **Update model** khi có version mới tốt hơn

---

## 📞 Hỗ trợ

Nếu gặp vấn đề:

1. Kiểm tra [Troubleshooting](#troubleshooting)
2. Xem logs: `logs/backend.log`
3. Kiểm tra [Issues](link-to-issues) trên GitHub
4. Tạo issue mới nếu chưa có

---

**Chúc bạn sử dụng thành công! 🎉**



