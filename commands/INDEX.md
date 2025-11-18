# 🔍 INDEX - TRA CỨU NHANH PROMPTS

## 📑 Tra cứu theo Tags

### #api - API Endpoints
- `api/violations.prompt.md` - Quản lý violations, CRUD operations
- `api/cameras.prompt.md` - Quản lý cameras, ROI config
- `api/streams.prompt.md` - Video streaming, MJPEG
- `api/detection.prompt.md` - Real-time detection endpoints

### #database - MongoDB Operations  
- `database/schema.prompt.md` - Schema violations, cameras, metadata
- `database/queries.prompt.md` - Aggregations, filters, pagination
- `database/migrations.prompt.md` - Update schema, data migration

### #detection - Computer Vision
- `detection/yolo.prompt.md` - YOLO v8 vehicle detection
- `detection/license-plate.prompt.md` - OCR biển số xe
- `detection/tracking.prompt.md` - DeepSORT tracking
- `detection/violations.prompt.md` - Logic phát hiện vi phạm

### #deployment - Triển khai
- `deployment/docker.prompt.md` - Docker compose, containers
- `deployment/single-server.prompt.md` - Deploy all-in-one
- `deployment/multi-server.prompt.md` - Microservices deploy
- `deployment/troubleshoot.prompt.md` - Debug deploy issues

### #frontend - React UI
- `frontend/components.prompt.md` - CameraTile, ViolationCard, etc
- `frontend/services.prompt.md` - API integration layer
- `frontend/state-management.prompt.md` - React hooks, context

### #workflow - Quy trình
- `workflows/new-feature.prompt.md` - Thêm feature mới
- `workflows/bug-fix.prompt.md` - Debug và fix bugs
- `workflows/code-review.prompt.md` - Review checklist
- `workflows/testing.prompt.md` - Unit & integration tests

---

## 🎯 Tra cứu theo Tác vụ

### "Tôi muốn thêm endpoint API mới"
→ `api/detection.prompt.md` hoặc `workflows/new-feature.prompt.md`

### "Fix lỗi không detect được biển số"
→ `detection/license-plate.prompt.md` + `workflows/bug-fix.prompt.md`

### "Deploy lên server mới"
→ `deployment/single-server.prompt.md` hoặc `deployment/multi-server.prompt.md`

### "Tối ưu performance tracking"
→ `detection/tracking.prompt.md` + `database/queries.prompt.md`

### "Thêm camera mới vào hệ thống"
→ `api/cameras.prompt.md` + `database/schema.prompt.md`

### "Fix bug streaming bị lag"
→ `api/streams.prompt.md` + `deployment/troubleshoot.prompt.md`

### "Update UI component"
→ `frontend/components.prompt.md`

### "Migration database schema"
→ `database/migrations.prompt.md`

---

## 🔥 Top Prompts (Dùng nhiều nhất)

1. **detection/violations.prompt.md** - Logic core phát hiện vi phạm
2. **api/violations.prompt.md** - API violations được dùng nhiều
3. **deployment/docker.prompt.md** - Deploy và troubleshoot
4. **detection/license-plate.prompt.md** - OCR biển số
5. **workflows/bug-fix.prompt.md** - Debug workflow

---

## 📊 Metadata Overview

### Inputs thường cần:
- Camera ID
- Video frame/stream URL
- ROI coordinates
- Detection thresholds
- Database connection string

### Tools/Libraries chính:
- YOLO v8 (ultralytics)
- OpenCV
- FastAPI
- MongoDB
- React + TypeScript
- Docker

### Output formats:
- JSON API responses
- Video streams (MJPEG)
- Detection results (bounding boxes)
- Violation records (database)

---

## 🚀 Quick Reference

| Tác vụ | Prompt File | Tags |
|--------|-------------|------|
| Phát hiện xe | `detection/yolo.prompt.md` | #detection #yolo |
| Nhận diện biển số | `detection/license-plate.prompt.md` | #detection #ocr |
| Tracking xe | `detection/tracking.prompt.md` | #detection #tracking |
| Phát hiện vi phạm | `detection/violations.prompt.md` | #detection #violations |
| API violations | `api/violations.prompt.md` | #api #violations |
| API cameras | `api/cameras.prompt.md` | #api #cameras |
| Video streaming | `api/streams.prompt.md` | #api #streaming |
| Database schema | `database/schema.prompt.md` | #database #schema |
| Deploy single | `deployment/single-server.prompt.md` | #deployment #docker |
| Deploy multi | `deployment/multi-server.prompt.md` | #deployment #microservices |
| React components | `frontend/components.prompt.md` | #frontend #react |
| Fix bugs | `workflows/bug-fix.prompt.md` | #workflow #debugging |
| Add feature | `workflows/new-feature.prompt.md` | #workflow #development |

---

## 💡 Tips cho AI Agent

1. **Đọc 2-3 prompts liên quan** thay vì đọc cả repo
2. **Check pitfalls** trước khi implement
3. **Follow checklist** để đảm bảo đầy đủ
4. **Xem examples** để hiểu context
5. **Combine prompts** cho tasks phức tạp

Ví dụ: "Thêm loại vi phạm mới" → Đọc:
- `detection/violations.prompt.md` (logic)
- `api/violations.prompt.md` (API)
- `database/schema.prompt.md` (schema)
- `workflows/new-feature.prompt.md` (process)
