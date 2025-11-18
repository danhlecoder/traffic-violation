# 🚀 Deploy Scripts - Multi Server

Scripts để deploy hệ thống lên 4 server riêng biệt.

---

## 📁 Danh Sách Scripts

| Script | Mô Tả | Chạy Trên |
|--------|-------|-----------|
| `deploy-server1-mongo.sh` | Deploy MongoDB + Mongo API | Server 1 |
| `deploy-server2-backend.sh` | Deploy Backend API (YOLO tích hợp) | Server 2 |
| `deploy-server3-frontend.sh` | Deploy Frontend Web | Server 3 |
| `deploy-server4-n8n.sh` | Deploy N8N Automation (optional) | Server 4 |

---

## ⚡ Cách Sử Dụng (Thủ Công - Khuyến Nghị)

### Bước 1: Cấu Hình IP

**Không cần chạy script tự động**, bạn tự sửa file config:

#### Backend (Server 2):
```bash
# Copy file mẫu
cp backend/.env.multi-server backend/.env

# Sửa IP
nano backend/.env
```

Sửa dòng:
```env
MONGO_API_URL=http://[IP_SERVER_1]:8002
```

#### Frontend (Server 3):
```bash
# Copy file mẫu
cp frontend/.env.example frontend/.env.production.local

# Sửa IP
nano frontend/.env.production.local
```

Sửa dòng:
```env
VITE_API_BASE_URL=http://[IP_SERVER_2]:8000
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

**Server 2 (Backend - YOLO tích hợp sẵn):**
```bash
ssh user@192.168.1.20
cd traffic-violation
bash deploy-scripts/deploy-server2-backend.sh
```

**Server 3 (Frontend):**
```bash
ssh user@192.168.1.30
cd traffic-violation
bash deploy-scripts/deploy-server3-frontend.sh
```

**Server 4 (N8N - Optional):**
```bash
ssh user@192.168.1.40
cd traffic-violation
docker compose -f docker-compose.n8n.yml up -d
```

### Bước 4: Truy Cập Hệ Thống

Mở trình duyệt: `http://192.168.1.30:3000`

---

## 🔧 Thay Đổi IP Sau Này

Nếu IP server thay đổi, chỉ cần:

1. Chạy lại `setup-multi-server.sh` với IP mới
2. Deploy lại Server 2 (Backend) và Server 3 (Frontend):
   ```bash
   # Server 2
   bash deploy-scripts/deploy-server2-backend.sh

   # Server 3
   bash deploy-scripts/deploy-server3-frontend.sh
   ```

---

## ⚠️ Lưu Ý Quan Trọng

### 1. Thứ Tự Deploy

**PHẢI** deploy theo đúng thứ tự:
1. Server 1 (MongoDB) - Chờ MongoDB khởi động
2. Server 2 (Backend) - Backend phụ thuộc MongoDB, YOLO tích hợp sẵn
3. Server 3 (Frontend) - Frontend phụ thuộc vào Backend
4. Server 4 (N8N - Optional) - Automation workflows

### 2. Firewall

Mở port trên firewall của từng server:

```bash
# Server 1
sudo ufw allow 27017/tcp  # MongoDB
sudo ufw allow 8002/tcp   # Mongo API

# Server 2
sudo ufw allow 8000/tcp   # Backend API (YOLO tích hợp)

# Server 3
sudo ufw allow 3000/tcp   # Frontend Web

# Server 4 (Optional)
sudo ufw allow 8001/tcp   # N8N Automation
```

### 3. Models YOLO

Server 2 (Backend) cần có 3 file model trong thư mục `backend/models/`:
- `best1.pt` - Phát hiện xe, mũ bảo hiểm, đèn giao thông, biển số
- `license_plate.pt` - Phát hiện biển số (backup)
- `number_license_model.pt` - OCR ký tự biển số

Upload 3 file này lên Server 2 trước khi deploy!

---

## 📊 Kiểm Tra Health

Test từng service sau khi deploy:

```bash
# MongoDB API
curl http://192.168.1.10:8002/health

# Backend API (YOLO tích hợp sẵn)
curl http://192.168.1.20:8000/api/cameras

# Frontend (mở trình duyệt)
http://192.168.1.30:3000

# N8N (Optional)
http://192.168.1.40:8001
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
