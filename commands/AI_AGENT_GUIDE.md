# 🤖 AI AGENT GUIDE - HƯỚNG DẪN TỔNG QUAN

## 🎯 Mục đích tài liệu này

Tài liệu này giúp AI Agent hiểu nhanh dự án **Traffic Violation Detection System** mà không cần đọc toàn bộ source code.

---

## 📚 Cách sử dụng Commands/

### Quy trình làm việc của Agent

1. **Nhận yêu cầu từ user**
2. **Tra cứu INDEX.md** → Tìm prompts liên quan theo tags
3. **Đọc 1-3 prompts** thay vì đọc cả repo
4. **Follow checklist** trong prompts
5. **Tránh pitfalls** đã được document
6. **Implement** dựa trên examples
7. **Test** theo test checklist

### Ví dụ Workflow

**User request**: "Fix bug license plate detection không chính xác"

**Agent workflow**:
```
1. Mở INDEX.md → Tìm tag #license-plate, #bug-fix
2. Đọc prompts:
   - detection/license-plate.prompt.md (hiểu module)
   - workflows/bug-fix.prompt.md (hiểu process)
3. Follow checklist:
   - Reproduce bug
   - Check preprocessing
   - Check OCR output
   - Validate format
4. Check pitfalls:
   - Tránh OCR raw image
   - Tránh threshold quá thấp
   - Không cache model
5. Implement fix
6. Test theo checklist
7. Commit theo format
```

---

## 🏗️ Kiến trúc Dự án

### Tổng quan High-Level

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────▶│   Backend    │─────▶│   MongoDB   │
│  (React)    │      │  (FastAPI)   │      │   Service   │
└─────────────┘      └──────┬───────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │     YOLO     │
                     │   Service    │
                     └──────────────┘
```

### Module Breakdown

#### 1. Frontend (React + TypeScript)
**Chức năng**: UI cho monitoring và quản lý
- Live camera streams
- Violations management
- Camera configuration
- Analytics dashboard

**Prompts liên quan**:
- `frontend/components.prompt.md`
- `frontend/services.prompt.md`

#### 2. Backend (FastAPI)
**Chức năng**: API server và business logic
- RESTful APIs (v1/)
- Service orchestration
- Stream processing
- Violations management

**Modules chính**:
- `api/v1/` - API endpoints
- `clients/` - Service clients (MongoDB, YOLO)
- `core/` - Core logic (detection, tracking, violations)
- `utils/` - Utilities (logging, camera, image)

**Prompts liên quan**:
- `api/*.prompt.md` - Từng API endpoint
- `detection/*.prompt.md` - Detection logic
- `workflows/*.prompt.md` - Development workflows

#### 3. MongoDB Service
**Chức năng**: Database storage
- Violations records
- Camera configurations
- System metadata

**Prompts liên quan**:
- `database/schema.prompt.md`
- `database/queries.prompt.md`

#### 4. YOLO Service
**Chức năng**: Vehicle detection
- Real-time object detection
- License plate detection
- Vehicle tracking

**Prompts liên quan**:
- `detection/yolo.prompt.md`
- `detection/license-plate.prompt.md`
- `detection/tracking.prompt.md`

---

## 📋 Chức năng Core

### 1. Detection Pipeline
**Flow**: Camera → Frames → YOLO → Tracking → Violations

**Prompts**: 
- `detection/yolo.prompt.md` - Vehicle detection
- `detection/license-plate.prompt.md` - Plate OCR
- `detection/tracking.prompt.md` - Object tracking
- `detection/violations.prompt.md` - Violation logic

### 2. Violations Management
**Flow**: Detect → Create → Store → Query → Update Status

**Prompts**:
- `api/violations.prompt.md` - API operations
- `database/schema.prompt.md` - Data structure

### 3. Camera Management
**Flow**: Add Camera → Configure ROI → Start Stream → Monitor

**Prompts**:
- `api/cameras.prompt.md` - Camera CRUD
- `api/streams.prompt.md` - Video streaming

### 4. Deployment
**Modes**: Single-server hoặc Multi-server

**Prompts**:
- `deployment/docker.prompt.md` - Docker setup
- `deployment/single-server.prompt.md` - All-in-one
- `deployment/multi-server.prompt.md` - Microservices

---

## 🎨 Tech Stack Overview

### Frontend
- **Framework**: React 18 + TypeScript
- **Build**: Vite
- **UI**: TailwindCSS + shadcn/ui
- **State**: React hooks + Context
- **HTTP**: Axios

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.10+
- **Async**: asyncio, uvicorn
- **Validation**: Pydantic

### Detection
- **Object Detection**: YOLO v8 (ultralytics)
- **OCR**: PaddleOCR / EasyOCR
- **Tracking**: DeepSORT
- **CV**: OpenCV

### Database
- **Primary**: MongoDB 7.0
- **Driver**: Motor (async PyMongo)

### Infrastructure
- **Containers**: Docker + Docker Compose
- **Orchestration**: Shell scripts
- **Deployment**: Multi-server capable

---

## 🔍 Tìm Prompt Nhanh

### Theo Module

| Module | Prompts |
|--------|---------|
| API Endpoints | `api/*.prompt.md` |
| Detection | `detection/*.prompt.md` |
| Database | `database/*.prompt.md` |
| Frontend | `frontend/*.prompt.md` |
| Deploy | `deployment/*.prompt.md` |
| Workflows | `workflows/*.prompt.md` |

### Theo Tác vụ

| Tác vụ | Prompts chính |
|--------|---------------|
| Thêm API endpoint | `api/violations.prompt.md`, `workflows/new-feature.prompt.md` |
| Fix detection bug | `detection/*.prompt.md`, `workflows/bug-fix.prompt.md` |
| Optimize performance | Module prompt + `workflows/testing.prompt.md` |
| Deploy hệ thống | `deployment/*.prompt.md` |
| Update database | `database/schema.prompt.md`, `database/migrations.prompt.md` |
| UI changes | `frontend/*.prompt.md` |

---

## ⚡ Quick Reference

### File Structure Checklist

```
traffic-violation/
├── frontend/              # React UI
│   ├── src/
│   │   ├── components/   # UI components
│   │   ├── pages/        # Page routes
│   │   ├── services/     # API clients
│   │   └── utils/        # Helpers
│   └── public/
│
├── backend/              # FastAPI server
│   ├── api/v1/          # API endpoints
│   ├── clients/         # Service clients
│   ├── core/            # Business logic
│   │   ├── detection/   # YOLO, filters
│   │   ├── license_plate/ # OCR
│   │   ├── tracking/    # Object tracking
│   │   ├── violations/  # Violation logic
│   │   └── streaming/   # Video streams
│   ├── config/          # Configuration
│   └── utils/           # Utilities
│
├── mongo-service/        # MongoDB container
├── yolo-service/         # YOLO container
├── deploy-scripts/       # Deployment automation
│
└── commands/            # AI Agent prompts (bạn đang ở đây)
    ├── api/
    ├── database/
    ├── detection/
    ├── deployment/
    ├── frontend/
    └── workflows/
```

### Environment Files

| File | Purpose |
|------|---------|
| `backend/.env.single-server` | Deploy tất cả trên 1 server |
| `backend/.env.multi-server` | Deploy microservices |
| `mongo-service/.env` | MongoDB configs |
| `yolo-service/.env` | YOLO service configs |
| `frontend/.env` | Frontend API URLs |

### Important Commands

| Task | Command |
|------|---------|
| Start single-server | `./run.sh` |
| Start MongoDB only | `docker-compose -f docker-compose.mongo.yml up` |
| Start YOLO only | `docker-compose -f docker-compose.yolo.yml up` |
| Start Backend only | `docker-compose -f docker-compose.backend.yml up` |
| View logs | `docker logs <container>` |
| Check containers | `docker ps` |

---

## 💡 Best Practices cho Agent

### 1. Đọc có chọn lọc
✅ **Làm**: Đọc 1-3 prompts liên quan
❌ **Tránh**: Đọc toàn bộ repo

### 2. Follow checklists
✅ **Làm**: Tick từng item trong checklist
❌ **Tránh**: Skip steps

### 3. Check pitfalls
✅ **Làm**: Review pitfalls section trước khi code
❌ **Tránh**: Implement mà không check common mistakes

### 4. Use examples
✅ **Làm**: Copy pattern từ examples
❌ **Tránh**: Invent own patterns

### 5. Test thoroughly
✅ **Làm**: Follow test checklist
❌ **Tránh**: Assume code works

### 6. Document changes
✅ **Làm**: Update prompts nếu thêm features
❌ **Tránh**: Leave prompts outdated

---

## 🚀 Common Scenarios

### Scenario 1: User muốn thêm loại vi phạm mới

**Prompts cần đọc**:
1. `detection/violations.prompt.md` - Hiểu violation logic
2. `database/schema.prompt.md` - Update schema
3. `api/violations.prompt.md` - API changes
4. `workflows/new-feature.prompt.md` - Development process

**Checklist**:
- [ ] Thêm violation type vào enum
- [ ] Update detection logic
- [ ] Update database schema
- [ ] Update API validation
- [ ] Update frontend UI
- [ ] Add tests
- [ ] Update documentation

### Scenario 2: Performance issue - Detection chậm

**Prompts cần đọc**:
1. `detection/yolo.prompt.md` - Check YOLO config
2. `detection/tracking.prompt.md` - Check tracking overhead
3. `deployment/docker.prompt.md` - Check resource allocation

**Debug checklist**:
- [ ] Check GPU utilization
- [ ] Check frame skip settings
- [ ] Check model size
- [ ] Check resolution settings
- [ ] Profile code với cProfile
- [ ] Monitor docker stats

### Scenario 3: Deploy lên production

**Prompts cần đọc**:
1. `deployment/multi-server.prompt.md` - Architecture
2. `deployment/docker.prompt.md` - Docker setup
3. `deployment/troubleshoot.prompt.md` - Common issues

**Deployment checklist**:
- [ ] Choose single vs multi-server
- [ ] Configure environment files
- [ ] Set up MongoDB server
- [ ] Deploy YOLO service
- [ ] Deploy Backend
- [ ] Deploy Frontend
- [ ] Configure domains/SSL
- [ ] Set up monitoring
- [ ] Test all endpoints

---

## 🎓 Learning Path cho New Agent

### Level 1: Hiểu Architecture
1. Đọc `README.md` (project root)
2. Đọc `INDEX.md` (commands/)
3. Đọc `AI_AGENT_GUIDE.md` (file này)

### Level 2: Hiểu Core Modules
1. `detection/violations.prompt.md`
2. `api/violations.prompt.md`
3. `database/schema.prompt.md`

### Level 3: Hiểu Workflows
1. `workflows/bug-fix.prompt.md`
2. `workflows/new-feature.prompt.md`
3. `workflows/testing.prompt.md`

### Level 4: Deep Dive
1. Đọc prompts của module đang work on
2. Check related prompts
3. Read actual code nếu cần details

---

## 📞 Support & Resources

### Khi nào cần đọc source code?
- Prompts chưa cover trường hợp cụ thể
- Cần hiểu implementation details
- Debug complex issues
- Performance optimization

### Khi nào update prompts?
- Thêm feature mới
- Fix bug phức tạp (add to pitfalls)
- Thay đổi architecture
- Phát hiện pattern mới

### Git Workflow
- Branch naming: `feat/`, `fix/`, `refactor/`
- Commit format: `type(scope): description`
- PR template: Include checklist

---

## 🏁 Conclusion

Thư mục `commands/` này được thiết kế để:
- ✅ Agent hiểu dự án nhanh chóng
- ✅ Tránh đọc toàn bộ source code
- ✅ Follow best practices
- ✅ Tránh common mistakes
- ✅ Implement consistent code

**Happy coding! 🚀**
