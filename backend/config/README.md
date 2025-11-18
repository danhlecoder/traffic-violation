# 📋 Cấu Hình Backend

## Cấu Trúc Phân Chia

### 🔧 `server.yaml` - Cấu Hình Tĩnh
**Mục đích:** Các thiết lập cố định, ít thay đổi, liên quan đến kiến trúc hệ thống

```yaml
✅ Server (host, port)
✅ Logging (level, file path)
✅ Địa chỉ API Services (YOLO, MongoDB)
✅ Database connection
✅ Model paths
```

**Khi nào sửa:**
- Deploy lên server mới
- Thay đổi địa chỉ services
- Cấu hình logging khác

---

### ⚙️ `.env` - Tham Số Điều Chỉnh
**Mục đích:** Các tham số có thể thay đổi để tối ưu hệ thống (tuning)

```bash
✅ Stream settings (FPS, quality, skip frames)
✅ Detection display (bbox thickness, font size)
✅ Density thresholds
✅ Tracking parameters (IOU, max age, min hits)
✅ Vision parameters (Canny, Hough, ROI detection)
```

**Khi nào sửa:**
- Tối ưu hiệu năng stream
- Điều chỉnh độ nhạy detection
- Fine-tune tracking behavior
- Cải thiện ROI detection

---

## 📊 So Sánh

| Tiêu Chí | `server.yaml` | `.env` |
|----------|---------------|--------|
| **Mục đích** | Infrastructure config | Performance tuning |
| **Tần suất thay đổi** | Hiếm (khi deploy) | Thường (khi optimize) |
| **Format** | YAML (có cấu trúc) | Key-Value đơn giản |
| **Nội dung** | URLs, paths, cố định | Numbers, thresholds |
| **Commit vào Git?** | ✅ Có | ⚠️ Tùy dự án |

---

## 🔄 Luồng Load Config

```
1. App khởi động
   ↓
2. Load server.yaml (cấu hình tĩnh)
   ↓
3. Load .env (tham số điều chỉnh)
   ↓
4. Validate settings
   ↓
5. App ready!
```

Code: `backend/config/config.py`
```python
class Settings:
    def __init__(self):
        self._load_yaml_config()  # server.yaml
        self._load_env_params()   # .env
        self._validate_settings()
```

---

## 📝 Ví Dụ Thực Tế

### Scenario 1: Deploy lên server mới
**File cần sửa:** `server.yaml`
```yaml
services:
  yolo_api: "http://192.168.1.100:8001"  # ← Đổi IP mới
  mongo_api: "http://192.168.1.101:8002"
```

### Scenario 2: Stream bị giật, muốn giảm FPS
**File cần sửa:** `.env`
```bash
STREAM_DEFAULT_FPS=30  # ← Giảm từ 60 xuống 30
STREAM_SKIP_FRAMES=2   # ← Skip 2 frames để tăng tốc
```

### Scenario 3: Detection quá nhạy, nhiều false positive
**File cần sửa:** `.env`
```bash
TRACKER_IOU_THRESHOLD=0.5  # ← Tăng từ 0.3 lên 0.5
VISION_CANNY_LOW=50        # ← Tăng threshold
```

---

## ✅ Best Practices

1. **Không hard-code** config trong code
2. **server.yaml** - commit vào Git (với placeholder cho production)
3. **.env** - thêm vào `.gitignore`, tạo `.env.example`
4. **Document** mọi thay đổi quan trọng
5. **Backup** config trước khi sửa

---

## 🚨 Lưu Ý

- **KHÔNG** để API keys, passwords trong Git
- **SỬ DỤNG** environment variables cho sensitive data
- **TEST** kỹ sau khi thay đổi config
- **BACKUP** config production trước khi deploy

---

*Generated: 2025-01-28*
