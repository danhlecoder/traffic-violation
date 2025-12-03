# 🚦 Hệ thống Phát hiện Vi phạm Giao thông

Hệ thống phát hiện và ghi nhận vi phạm giao thông tự động sử dụng YOLO, Computer Vision và AI.

![Python](https://img.shields.io/badge/python-3.10%2B-brightgreen)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688)
![React](https://img.shields.io/badge/React-18-blue)
![YOLO](https://img.shields.io/badge/YOLO-v8-yellow)

---

## 📋 Tính năng chính

### 🎯 Phát hiện Vi phạm
- **Vượt đèn đỏ**: Tự động phát hiện xe vượt đèn đỏ (có lọc xe rẽ phải hợp lệ)
- **Không đội mũ bảo hiểm**: Phát hiện xe máy không đội mũ
- **Quá tốc độ**: Đo tốc độ và cảnh báo vi phạm

### 🤖 AI & Computer Vision
- YOLO phát hiện 10 loại đối tượng (xe, mũ, đèn tín hiệu, biển số)
- ByteTrack theo dõi phương tiện
- YOLO OCR nhận dạng biển số xe
- Tự động phát hiện vạch dừng

### 💻 Giao diện & Quản lý
- Dashboard theo dõi real-time nhiều camera
- Quản lý và xác nhận vi phạm
- Báo cáo thống kê với biểu đồ
- Tích hợp Discord/N8N để gửi thông báo

---

## 🚀 Cách chạy

### Yêu cầu
- Docker & Docker Compose
- Python 3.10+ (nếu chạy local)
- Node.js 18+ (nếu dev frontend)

### Bước 1: Chuẩn bị Model

```bash
# Tạo thư mục models (nếu chưa có)
mkdir -p backend/models

# Đặt 2 file model vào thư mục:
# - best.pt (YOLO detection)
# - license_plate.pt (YOLO OCR biển số)
```

### Bước 2: Chạy hệ thống

```bash
# Clone repository
git clone <repo-url>
cd traffic-violation

# Chạy tất cả services
bash run.sh up

# Hoặc chạy từng service riêng:
docker compose -f docker-compose.mongo.yml up -d       # MongoDB
docker compose -f docker-compose.backend.yml up -d     # Backend API
docker compose -f docker-compose.frontend.yml up -d    # Frontend
docker compose -f docker-compose.n8n.yml up -d         # N8N (optional)
```

### Bước 3: Truy cập

```
Frontend:  http://localhost:3000
Backend:   http://localhost:8000
API Docs:  http://localhost:8000/docs
MongoDB:   http://localhost:8002
N8N:       http://localhost:8001
```

### Dừng hệ thống

```bash
bash run.sh down
```

---

## 🤖 N8N Automation (Optional)

N8N để tự động gửi thông báo khi có vi phạm được xác nhận.

### Cách setup:

1. **Truy cập N8N**: http://localhost:8001
2. **Đăng ký tài khoản** (lần đầu tiên)
3. **Import workflow**:
   - Vào menu → Import workflow
   - Chọn file: `n8n/workflows/chat discord.json`
   - Save và Activate workflow
4. **Cấu hình Discord webhook** trong workflow nếu muốn dùng

### Test thông báo:

```bash
bash test_n8n_webhook.sh
```

---

## 📡 API Endpoints

### Streaming
```
GET /api/stream?src={rtsp_url}&fps=30&detection=true
```

### Cameras
```
GET    /api/cameras           # Danh sách camera
POST   /api/cameras           # Thêm camera
DELETE /api/cameras/{id}      # Xóa camera
```

### Violations
```
GET /api/violations                    # Danh sách vi phạm
PUT /api/violations/{track_id}         # Cập nhật vi phạm
```

Xem đầy đủ: http://localhost:8000/docs

---

## 🛠️ Tech Stack

- **Backend**: FastAPI, YOLO v8, ByteTrack, OpenCV, PyTorch
- **Frontend**: React 18, TypeScript, Ant Design, Zustand
- **Database**: MongoDB
- **Automation**: N8N
- **DevOps**: Docker, Docker Compose

---

## 📁 Cấu trúc Project

```
traffic-violation/
├── backend/              # FastAPI backend
│   ├── api/             # REST API endpoints
│   ├── core/            # Core logic (detection, tracking, violations)
│   ├── config/          # Configuration
│   └── models/          # YOLO model files
├── frontend/            # React frontend
│   └── src/
│       ├── pages/       # LiveMonitor, Violations, Reports, Settings
│       └── components/  # UI components
├── mongo-service/       # MongoDB API service
├── n8n/                 # N8N workflows
│   └── workflows/       # Import file JSON vào đây
└── docker-compose.*.yml # Docker configs
```

---

## 🐛 Troubleshooting

### Model không tìm thấy
```bash
# Kiểm tra file tồn tại
ls backend/models/best1.pt
ls backend/models/license_plate.pt
```

### MongoDB không kết nối được
```bash
# Kiểm tra container đang chạy
docker compose ps

# Restart MongoDB
docker compose -f docker-compose.mongo.yml restart
```

### Xem logs
```bash
# Tất cả services
docker compose logs -f

# Một service cụ thể
docker compose logs -f backend
```

### Rebuild từ đầu
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

## 📝 License



---
