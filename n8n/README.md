# 🤖 N8N Automation & Workflows

N8N là công cụ workflow automation mạnh mẽ giúp tự động hóa các tác vụ trong hệ thống phát hiện vi phạm giao thông.

---

## 📋 Thông tin kết nối

- **URL**: `http://192.168.1.43:8001`
- **Username**: `admin`
- **Password**: `admin123` (nên đổi trong production)
- **Port**: `8001` (internal: 5678)
- **Timezone**: `Asia/Ho_Chi_Minh`

---

## 🚀 Cách sử dụng

### 1. Truy cập N8N

```bash
# Mở trình duyệt
http://192.168.1.43:8001

# Đăng nhập với:
# - Username: admin
# - Password: admin123
```

### 2. Kết nối với Backend API

Trong N8N workflow, sử dụng **HTTP Request** node:

```
URL: http://backend:8000/api/cameras
Method: GET
Authentication: None (nếu có thêm auth sau này)
```

### 3. Kết nối với MongoDB

Sử dụng **MongoDB** node với thông tin:

```
Connection String: mongodb://admin:admin123@mongo:27017/traffic?authSource=admin
Database: traffic
```

---

## 💡 Ví dụ Workflows

### Workflow 1: Gửi thông báo khi có vi phạm mới

```
1. Webhook (nhận từ Backend khi có vi phạm)
   ↓
2. Format dữ liệu vi phạm
   ↓
3. Gửi thông báo qua:
   - Zalo (HTTP Request đến Zalo API)
   - Email (SMTP node)
   - Telegram (Telegram node)
```

### Workflow 2: Backup dữ liệu định kỳ

```
1. Schedule Trigger (mỗi ngày 00:00)
   ↓
2. MongoDB node (export violations)
   ↓
3. Format JSON/CSV
   ↓
4. Upload lên Google Drive/Dropbox
   ↓
5. Gửi email báo cáo
```

### Workflow 3: Tổng hợp báo cáo tuần

```
1. Schedule Trigger (Chủ nhật hàng tuần)
   ↓
2. MongoDB Aggregate (thống kê vi phạm)
   ↓
3. Tạo báo cáo HTML/PDF
   ↓
4. Gửi email cho quản lý
```

### Workflow 4: Xử lý ảnh vi phạm

```
1. Webhook (nhận ảnh từ Backend)
   ↓
2. Resize/Optimize ảnh
   ↓
3. Upload lên Cloud Storage
   ↓
4. Cập nhật URL trong MongoDB
```

---

## 🔌 Tích hợp với Backend

### Backend gửi webhook đến N8N

Trong code Backend Python, thêm logic gửi webhook:

```python
import httpx

async def notify_n8n_new_violation(violation_data: dict):
    """Gửi thông báo vi phạm mới đến N8N"""
    webhook_url = "http://n8n:5678/webhook/new-violation"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                webhook_url,
                json=violation_data,
                timeout=5.0
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Lỗi gửi webhook đến N8N: {e}")
            return False
```

### N8N gọi API Backend

Sử dụng **HTTP Request** node trong workflow:

```
URL: http://backend:8000/api/violations
Method: GET/POST
Headers:
  Content-Type: application/json
Body:
  {
    "camera_id": "cam001",
    "violation_type": "red_light"
  }
```

---

## 📁 Quản lý Workflows

### Export workflow

1. Mở workflow trong N8N
2. Click **Export** → **Download**
3. Lưu file `.json` vào thư mục `n8n/workflows/`

### Import workflow

1. Click **Import** trong N8N
2. Chọn file `.json` từ `n8n/workflows/`
3. Activate workflow

### Lưu workflow vào Git

```bash
# Workflows được tự động mount vào:
# ./n8n/workflows → /home/node/.n8n/workflows trong container

# Commit vào Git:
git add n8n/workflows/
git commit -m "Thêm workflow tự động thông báo vi phạm"
```

---

## 🛠️ Quản lý N8N

### Khởi động N8N

```bash
# Khởi động tất cả services (bao gồm N8N)
bash run.sh up

# Hoặc chỉ khởi động N8N
docker compose -f docker-compose.n8n.yml up -d
```

### Dừng N8N

```bash
# Dừng tất cả services
bash run.sh down

# Hoặc chỉ dừng N8N
docker compose -f docker-compose.n8n.yml down
```

### Xem logs

```bash
# Xem logs real-time
docker compose -f docker-compose.n8n.yml logs -f

# Xem logs của container
docker logs traffic_n8n -f
```

### Restart N8N

```bash
docker compose -f docker-compose.n8n.yml restart
```

### Kiểm tra health

```bash
curl http://192.168.1.43:8001/healthz
```

---

## 🔧 Cấu hình nâng cao

### Thay đổi thông tin đăng nhập

Sửa file `docker-compose.n8n.yml`:

```yaml
environment:
  - N8N_BASIC_AUTH_USER=your_username
  - N8N_BASIC_AUTH_PASSWORD=your_secure_password
```

Sau đó restart:

```bash
docker compose -f docker-compose.n8n.yml down
docker compose -f docker-compose.n8n.yml up -d
```

### Thay đổi Webhook URL

Nếu deploy production với domain/IP khác:

```yaml
environment:
  - WEBHOOK_URL=http://your-domain.com:8001/
```

### Tắt xác thực (KHÔNG khuyến nghị)

```yaml
environment:
  - N8N_BASIC_AUTH_ACTIVE=false
```

### Cấu hình data retention

```yaml
environment:
  - EXECUTIONS_DATA_PRUNE=true
  - EXECUTIONS_DATA_MAX_AGE=168  # Giữ logs 7 ngày (168 giờ)
```

---

## 📊 Nodes phổ biến

### Webhook Node
Nhận HTTP requests từ hệ thống khác

### HTTP Request Node
Gọi API (Backend, Zalo, Google, v.v.)

### MongoDB Node
Truy vấn và thao tác MongoDB

### Schedule Trigger Node
Chạy workflow theo lịch (cron)

### Function Node
Xử lý logic bằng JavaScript

### IF/Switch Node
Điều kiện phân nhánh

### Email Node (SMTP)
Gửi email thông báo

### Google Sheets Node
Xuất dữ liệu ra Google Sheets

### Telegram Node
Gửi thông báo qua Telegram Bot

---

## 🐛 Troubleshooting

### N8N không khởi động được

```bash
# Kiểm tra logs
docker compose -f docker-compose.n8n.yml logs

# Kiểm tra port có bị chiếm không
sudo netstat -tlnp | grep 8001

# Restart service
docker compose -f docker-compose.n8n.yml restart
```

### Không kết nối được MongoDB

Kiểm tra:
1. MongoDB container đang chạy: `docker ps | grep mongo`
2. Connection string đúng: `mongodb://admin:admin123@mongo:27017/traffic?authSource=admin`
3. Network đúng: cả N8N và MongoDB phải cùng network `traffic_net`

### Webhook không hoạt động

```bash
# Test webhook từ bên ngoài
curl -X POST http://192.168.1.43:8001/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

# Kiểm tra URL webhook trong N8N:
# - Production: http://192.168.1.43:8001/webhook/your-path
# - Test: http://192.168.1.43:8001/webhook-test/your-path
```

### Workflow không chạy tự động

Kiểm tra:
1. Workflow đã được **Activate** chưa
2. Schedule trigger có đúng timezone không
3. Xem logs executions trong N8N UI

---

## 📚 Tài liệu tham khảo

- **N8N Official Docs**: https://docs.n8n.io/
- **N8N Community**: https://community.n8n.io/
- **N8N Workflow Templates**: https://n8n.io/workflows/

---

## 🔒 Bảo mật

### Production Checklist

- [ ] Đổi mật khẩu mặc định
- [ ] Sử dụng HTTPS với SSL certificate
- [ ] Giới hạn IP truy cập (firewall)
- [ ] Backup dữ liệu định kỳ
- [ ] Cấu hình rate limiting
- [ ] Sử dụng secrets management cho API keys

### Backup dữ liệu N8N

```bash
# Backup volume
docker run --rm \
  -v traffic_violation_n8n_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/n8n-backup-$(date +%Y%m%d).tar.gz /data

# Restore
docker run --rm \
  -v traffic_violation_n8n_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/n8n-backup-YYYYMMDD.tar.gz -C /
```

---

## 💡 Tips & Best Practices

1. **Đặt tên workflow rõ ràng**: "Thông báo vi phạm mới - Zalo"
2. **Thêm Error Workflow**: Xử lý lỗi tập trung
3. **Sử dụng Environment Variables**: Lưu API keys
4. **Test workflow**: Dùng Test mode trước khi Activate
5. **Document workflows**: Thêm Sticky Note để giải thích logic
6. **Version control**: Export và commit workflows vào Git
7. **Monitor executions**: Kiểm tra logs định kỳ
8. **Set timeouts**: Tránh workflows chạy mãi

---

## 🎯 Roadmap

- [ ] Template workflows cho các use cases phổ biến
- [ ] Tích hợp Zalo OA API
- [ ] Workflow tự động backup MongoDB
- [ ] Dashboard báo cáo vi phạm real-time
- [ ] AI-powered violation classification
- [ ] Multi-tenant workflows

---

**Version**: 1.0.0
**Last Updated**: November 2025
**Maintainer**: Traffic Violation Team



