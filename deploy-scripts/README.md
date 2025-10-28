# 🚀 Deploy Scripts - Multi Server

Scripts để deploy hệ thống lên 4 server riêng biệt.

---

## 📁 Danh Sách Scripts

| Script | Mô Tả | Chạy Trên |
|--------|-------|-----------|
| `deploy-server1-mongo.sh` | Deploy MongoDB + Mongo API | Server 1 |
| `deploy-server2-yolo.sh` | Deploy YOLO Detection Service | Server 2 |
| `deploy-server3-backend.sh` | Deploy Backend API | Server 3 |
| `deploy-server4-frontend.sh` | Deploy Frontend Web | Server 4 |

---

## ⚡ Cách Sử Dụng (Thủ Công - Khuyến Nghị)

### Bước 1: Cấu Hình IP

**Không cần chạy script tự động**, bạn tự sửa file config:

#### Backend (Server 3):
```bash
# Copy file mẫu
cp backend/.env.multi-server backend/.env

# Sửa IP
nano backend/.env
```

Sửa 2 dòng:
```env
YOLO_API_URL=http://[IP_SERVER_2]:8001
MONGO_API_URL=http://[IP_SERVER_1]:8002
```

#### Frontend (Server 4):
```bash
# Copy file mẫu
cp frontend/.env.example frontend/.env.production.local

# Sửa IP
nano frontend/.env.production.local
```

Sửa dòng:
```env
VITE_API_BASE_URL=http://[IP_SERVER_3]:8000
```

📖 **Chi tiết:** Xem file `HUONG_DAN_DOI_IP.md`

### Bước 2: Upload Code

Upload toàn bộ project lên từng server (dùng git, scp, rsync, v.v.)

```bash
# Ví dụ: Upload code lên Server 1
scp -r traffic-violation user@192.168.1.10:~/
```

### Bước 3: Deploy Từng Server

**Server 1 (MongoDB):**
```bash
ssh user@192.168.1.10
cd traffic-violation
bash deploy-scripts/deploy-server1-mongo.sh
```

**Server 2 (YOLO):**
```bash
ssh user@192.168.1.20
cd traffic-violation
bash deploy-scripts/deploy-server2-yolo.sh
```

**Server 3 (Backend):**
```bash
ssh user@192.168.1.30
cd traffic-violation
bash deploy-scripts/deploy-server3-backend.sh
```

**Server 4 (Frontend):**
```bash
ssh user@192.168.1.40
cd traffic-violation
bash deploy-scripts/deploy-server4-frontend.sh
```

### Bước 4: Truy Cập Hệ Thống

Mở trình duyệt: `http://192.168.1.40:3000`

---

## 🔧 Thay Đổi IP Sau Này

Nếu IP server thay đổi, chỉ cần:

1. Chạy lại `setup-multi-server.sh` với IP mới
2. Deploy lại Server 3 (Backend) và Server 4 (Frontend):
   ```bash
   # Server 3
   bash deploy-scripts/deploy-server3-backend.sh
   
   # Server 4
   bash deploy-scripts/deploy-server4-frontend.sh
   ```

---

## ⚠️ Lưu Ý Quan Trọng

### 1. Thứ Tự Deploy

**PHẢI** deploy theo đúng thứ tự:
1. Server 1 (MongoDB) - Chờ MongoDB khởi động
2. Server 2 (YOLO) - Chờ YOLO load model
3. Server 3 (Backend) - Backend phụ thuộc vào 2 service trên
4. Server 4 (Frontend) - Frontend phụ thuộc vào Backend

### 2. Firewall

Mở port trên firewall của từng server:

```bash
# Server 1
sudo ufw allow 27017/tcp  # MongoDB
sudo ufw allow 8002/tcp   # Mongo API

# Server 2
sudo ufw allow 8001/tcp   # YOLO API

# Server 3
sudo ufw allow 8000/tcp   # Backend API

# Server 4
sudo ufw allow 3000/tcp   # Frontend Web
```

### 3. Models YOLO

Server 2 cần có 2 file model:
- `backend/models/best1.pt` (phát hiện xe, biển số)
- `backend/models/license_plate.pt` (OCR biển số)

Upload 2 file này lên Server 2 trước khi deploy!

---

## 📊 Kiểm Tra Health

Test từng service sau khi deploy:

```bash
# MongoDB API
curl http://192.168.1.10:8002/health

# YOLO API
curl http://192.168.1.20:8001/health

# Backend API
curl http://192.168.1.30:8000/api/cameras

# Frontend (mở trình duyệt)
http://192.168.1.40:3000
```

---

## 🔄 Cập Nhật Code

Khi có code mới:

```bash
# Trên từng server
git pull
bash deploy-scripts/deploy-server[X]-[service].sh
```

---

## 🛑 Stop All Services

```bash
# Chạy trên từng server
docker compose down
```

---

## 📖 Chi Tiết

Xem file `DEPLOY_MULTI_SERVER.md` để biết thêm chi tiết.
