# Hướng dẫn Cấu hình

## Nguyên tắc

### 1. `.env` - Tham số ĐỘNG (Dynamic Parameters)
Các tham số **có thể thay đổi thường xuyên** để điều chỉnh:
- FPS, quality
- Confidence, IOU threshold  
- Ngưỡng phân loại mật độ
- Tham số vision detection

**Đặc điểm:**
- ✅ Thay đổi nhiều
- ✅ Điều chỉnh performance
- ✅ Fine-tuning

### 2. `backend/config/server.yaml` - Tham số TĨNH (Static Config)
Các tham số **ít thay đổi**:
- Server (host, port, CORS)
- Database connection
- Logging config
- Model paths
- Device

**Đặc điểm:**
- ✅ Infrastructure config
- ✅ Ít thay đổi
- ✅ Environment-specific

### 3. KHÔNG CÓ DEFAULT VALUES
- ❌ Không có giá trị mặc định
- ✅ Bắt buộc phải config
- ✅ Không có thì để trống

---

## Cấu hình `.env`

**Tạo file:**
```bash
cp .env.example .env
```

**Ví dụ cấu hình:**
```env
# YOLO Detection
YOLO_CONFIDENCE=0.25
YOLO_IOU_THRESHOLD=0.45
YOLO_MAX_DETECTIONS=100

# Stream
STREAM_DEFAULT_FPS=15
STREAM_DEFAULT_QUALITY=70
STREAM_SKIP_FRAMES=2
STREAM_DETECTION_WIDTH=640

# Detection Display
BBOX_THICKNESS=2
FONT_SCALE=0.6
FONT_THICKNESS=2

# Vehicle Density
DENSITY_THRESHOLD_LOW=5
DENSITY_THRESHOLD_MEDIUM=15

# Vision - Stop Line Detection
VISION_CANNY_LOW=50
VISION_CANNY_HIGH=50
VISION_HOUGH_THRESHOLD=100
VISION_MIN_LINE_LEN_FACTOR=0.25
VISION_MAX_GAP_FACTOR=0.02
VISION_MIN_LINE_LEN_MIN_PX=60
VISION_MAX_GAP_MIN_PX=10
VISION_ANGLE_MAX_DEG=10.0
VISION_CENTER_BIAS_RATIO=0.35
VISION_BOTTOM_MIN_Y_RATIO=0.60
```

---

## Cấu hình `server.yaml`

```yaml
# Static Configuration

# Server
server:
  host: "0.0.0.0"
  port: 8000
  allowed_origins: "*"

# Logging
logging:
  level: INFO
  file: /app/logs/backend.log
  max_bytes: 10485760
  backup_count: 5

# YOLO Model
yolo:
  model_path: /app/backend/model/best.pt
  device: cpu

# Database
database:
  mongo_camera:
    host: mongo
    port: 27017
    database: traffic
    username: ""
    password: ""
    authSource: admin
```

---

## Cách điều chỉnh

### Tăng độ chính xác YOLO
**Sửa:** `.env`
```env
YOLO_CONFIDENCE=0.35  # Từ 0.25 → 0.35
```

### Thay đổi database
**Sửa:** `server.yaml`
```yaml
database:
  mongo_camera:
    host: new-mongo-host
    port: 27017
```

### Tăng FPS stream
**Sửa:** `.env`
```env
STREAM_DEFAULT_FPS=30  # Từ 15 → 30
```

---

## Kiểm tra config

```bash
# Xem config đang dùng
docker compose logs backend | grep "Server ready"

# Restart sau khi thay đổi
docker compose restart backend
```
