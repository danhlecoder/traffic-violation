# 📝 Changelog - Traffic Violation Detection

## [1.0.0] - 2025-10-15

### ✨ Tính năng mới

#### YOLO Detection Integration
- ✅ Tích hợp YOLOv8 để detect objects trên stream
- ✅ Hỗ trợ 10 classes: bus, car, motorcycle, truck, helmet, no_helmet, license_plate, light_red, light_yellow, light_green
- ✅ Vẽ bounding boxes và labels (tiếng Việt) lên frame
- ✅ Singleton pattern cho YOLO detector (load model 1 lần)
- ✅ Cấu hình confidence, IOU threshold qua environment variables
- ✅ Hỗ trợ cả CPU và GPU (CUDA)

#### Configuration Management
- ✅ Centralized configuration trong `core/config.py`
- ✅ Load từ environment variables (`.env`)
- ✅ Fallback sang YAML config
- ✅ Type-safe settings
- ✅ File `.env.example` mẫu

#### Streaming Enhancements
- ✅ Tham số `detection` để bật/tắt YOLO detection
- ✅ Tùy chỉnh FPS, quality cho mỗi stream
- ✅ Logging chi tiết
- ✅ Error handling tốt hơn
- ✅ Auto reconnect khi mất kết nối

### 🏗️ Refactoring

#### Cấu trúc thư mục mới
```
backend/
├── core/              # 🆕 Configuration & Constants
├── schemas/           # 🆕 Pydantic models
├── models/            # 🆕 AI models (YOLO)
├── routers/           # ✨ Improved
├── src/
│   ├── rtsp_stream/   # ✨ YOLO integration
│   ├── services/      # ✨ Refactored
│   └── utils/         # ✨ Improved
```

#### Code Quality
- ✅ Type hints cho tất cả functions
- ✅ Docstrings đầy đủ (Google style)
- ✅ Error handling comprehensive
- ✅ Logging với 3 loggers: app, stream, detector
- ✅ Constants management
- ✅ Comments bằng tiếng Việt

#### Database Service
- ✅ Refactor `db.py` sử dụng settings
- ✅ Thêm `close_connection()` cho cleanup
- ✅ Better error handling
- ✅ Connection pooling

#### Logging
- ✅ 3 loggers riêng biệt: app, stream, detector
- ✅ Rotating file handler
- ✅ Configurable via settings
- ✅ Emoji cho dễ đọc (✓, ✗, ⚠, 🚀, 🛑)

### 📦 Dependencies

#### Thêm mới
- `ultralytics==8.3.62` - YOLO detection
- `torch>=2.0.0` - PyTorch (YOLO dependency)
- `torchvision>=0.15.0` - Torchvision
- `pydantic==2.10.6` - Schema validation

### 📚 Documentation

#### Thêm mới
- ✅ `backend/README.md` - Backend documentation
- ✅ `REFACTOR_SUMMARY.md` - Chi tiết refactor
- ✅ `HUONG_DAN_SU_DUNG.md` - Hướng dẫn sử dụng đầy đủ
- ✅ `.env.example` - Environment variables mẫu
- ✅ `test_yolo.py` - Script test YOLO
- ✅ `CHANGELOG.md` - File này

#### Cải thiện
- ✅ Docstrings cho tất cả modules, classes, functions
- ✅ Type hints rõ ràng
- ✅ Comments tiếng Việt

### 🔧 API Changes

#### Streams Router
**Thay đổi:**
- Endpoint `/api/stream` thêm tham số `detection`

**Trước:**
```
GET /api/stream?src={url}&fps={fps}&quality={quality}
```

**Sau:**
```
GET /api/stream?src={url}&fps={fps}&quality={quality}&detection={bool}
```

**Breaking:** Không có (tham số `detection` mặc định là `true`)

#### Cameras Router
**Thay đổi:**
- Sử dụng schemas từ `schemas/camera.py`
- Thêm comprehensive error handling
- Logging chi tiết hơn

**Breaking:** Không có

### 🐛 Bug Fixes

- ✅ Fix import paths trong `detec_line.py`
- ✅ Fix MongoDB connection với settings
- ✅ Fix logger initialization
- ✅ Fix streaming reconnection logic

### ⚡ Performance

- ✅ Model loading chỉ 1 lần (singleton)
- ✅ Có thể tắt detection để stream nhanh hơn
- ✅ Configurable FPS và quality
- ✅ GPU support cho detection nhanh hơn

### 🔒 Security

- ✅ Không hardcode credentials
- ✅ Sử dụng environment variables
- ✅ Input validation với Pydantic
- ✅ Error messages không leak sensitive info

---

## [0.1.0] - Trước refactor

### Tính năng
- ✅ RTSP/HTTP streaming
- ✅ Camera management
- ✅ Stop line detection
- ✅ MongoDB integration
- ✅ CORS support

### Hạn chế
- ❌ Không có object detection
- ❌ Cấu trúc chưa tối ưu
- ❌ Thiếu documentation
- ❌ Logging đơn giản
- ❌ Hardcoded values

---

## 🔮 Roadmap

### v1.1.0 (Sắp tới)
- [ ] Violations detection logic
- [ ] Save violations to database
- [ ] Alert via Zalo/Email
- [ ] Analytics dashboard
- [ ] Multi-camera parallel processing

### v1.2.0 (Tương lai)
- [ ] License plate recognition
- [ ] Speed detection
- [ ] Vehicle counting
- [ ] Heatmap visualization
- [ ] Reports generation

### v2.0.0 (Long-term)
- [ ] Real-time analytics
- [ ] Machine learning pipeline
- [ ] Model training interface
- [ ] Mobile app
- [ ] Cloud deployment

---

## 🙏 Credits

- **Refactor & YOLO Integration**: AI Assistant (Claude)
- **Original Codebase**: Development Team
- **YOLO Model**: Ultralytics YOLOv8
- **Frameworks**: FastAPI, OpenCV, PyTorch

---

**Ngày release**: 15/10/2025
**Version**: 1.0.0
**Status**: ✅ Production Ready



