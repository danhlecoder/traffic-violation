# ⚡ Quick Start - Traffic Violation Detection

## 🚀 Khởi động nhanh trong 5 phút

### Bước 1: Chuẩn bị Model YOLO (1 phút)

```bash
# Đặt file best.pt vào thư mục model
mkdir -p backend/model
cp /path/to/your/best.pt backend/model/

# Kiểm tra
ls -lh backend/model/best.pt
```

### Bước 2: Cài đặt Dependencies (2 phút)

```bash
# Cài đặt Python packages
pip install -r requirements.txt

# Hoặc sử dụng Docker
docker compose up -d --build
```

### Bước 3: Cấu hình (1 phút)

Tạo file `.env` từ template:

```bash
# Copy file mẫu
cp .env.example .env

# Chỉnh sửa (nếu cần)
nano .env
```

**Cấu hình tối thiểu:**
```bash
YOLO_MODEL_PATH=/app/backend/model/best.pt
MONGO_HOST=mongo
YOLO_DEVICE=cpu
```

### Bước 4: Chạy Server (1 phút)

```bash
# Chạy với Docker (khuyến nghị)
docker compose up -d

# Hoặc chạy trực tiếp
uvicorn backend.app:app --reload
```

### Bước 5: Test (30 giây)

```bash
# Health check
curl http://localhost:8000/api/health

# Test YOLO
python test_yolo.py
```

---

## 🎯 Sử dụng ngay

### Stream với Detection

Mở trình duyệt và truy cập:

```
http://localhost:5173
```

Hoặc test trực tiếp API:

```html
<img src="http://localhost:8000/api/stream?src=rtsp://your-camera-url" />
```

### API Endpoints

**Thêm camera:**
```bash
curl -X POST http://localhost:8000/api/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "id": "cam001",
    "name": "Camera 1",
    "rtsp": "rtsp://camera.com/stream",
    "location": "Ngã tư ABC"
  }'
```

**Stream với detection:**
```
http://localhost:8000/api/stream?src=rtsp://camera.com/stream&detection=true
```

---

## 📊 Detection Classes

Model detect 10 loại đối tượng:

| Icon | Class | Tiếng Việt |
|------|-------|-----------|
| 🚌 | bus | Xe buýt |
| 🚗 | car | Ô tô |
| 🏍️ | motorcycle | Xe máy |
| 🚚 | truck | Xe tải |
| 🪖 | helmet | Mũ bảo hiểm |
| 👤 | no_helmet | Không mũ |
| 🔢 | license_plate | Biển số |
| 🔴 | light_red | Đèn đỏ |
| 🟡 | light_yellow | Đèn vàng |
| 🟢 | light_green | Đèn xanh |

---

## 🔧 Troubleshooting

### Lỗi thường gặp

**1. Model not found**
```bash
# Kiểm tra file
ls backend/model/best.pt

# Sửa path trong .env
YOLO_MODEL_PATH=/app/backend/model/best.pt
```

**2. MongoDB connection failed**
```bash
# Chạy MongoDB
docker compose up -d mongo

# Hoặc
sudo systemctl start mongodb
```

**3. Import errors**
```bash
# Cài đặt lại dependencies
pip install -r requirements.txt --force-reinstall
```

---

## 📚 Tài liệu đầy đủ

- **Backend API**: `backend/README.md`
- **Hướng dẫn chi tiết**: `HUONG_DAN_SU_DUNG.md`
- **Refactor summary**: `REFACTOR_SUMMARY.md`
- **Changelog**: `CHANGELOG.md`

---

## 🎉 Done!

Hệ thống đã sẵn sàng. Truy cập:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

Enjoy! 🚀



