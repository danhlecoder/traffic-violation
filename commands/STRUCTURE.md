# 📁 CẤU TRÚC THỨ MỤC COMMANDS - TỔNG KẾT

## 🎯 Tổng quan

Thư mục `commands/` chứa **prompts/rules nhỏ gọn** giúp AI Agent hiểu nhanh dự án mà không cần đọc toàn bộ source code.

---

## 🌳 Cấu trúc Cây Thư Mục

```
commands/
│
├── 📄 README.md                         # Hướng dẫn sử dụng commands
├── 📄 INDEX.md                          # Index tra cứu nhanh theo tags
├── 📄 AI_AGENT_GUIDE.md                 # Guide tổng quan cho Agent
├── 📄 STRUCTURE.md                      # File này - cấu trúc chi tiết
│
├── 📁 api/                              # Prompts về API endpoints
│   ├── violations.prompt.md            ✅ CRUD violations, filters, pagination
│   ├── cameras.prompt.md               ✅ CRUD cameras, ROI config, stream test
│   ├── streams.prompt.md               📝 TODO: MJPEG streaming, WebSocket
│   └── detection.prompt.md             📝 TODO: Real-time detection API
│
├── 📁 database/                         # Prompts về MongoDB
│   ├── schema.prompt.md                ✅ Collections, indexes, validation
│   ├── queries.prompt.md               📝 TODO: Aggregations, common patterns
│   └── migrations.prompt.md            📝 TODO: Schema updates, data migration
│
├── 📁 detection/                        # Prompts về Computer Vision
│   ├── yolo.prompt.md                  ✅ Vehicle detection, YOLO config
│   ├── license-plate.prompt.md         ✅ OCR, preprocessing, validation
│   ├── tracking.prompt.md              ✅ DeepSORT, ROI tracking
│   └── violations.prompt.md            📝 TODO: Violation logic, rules engine
│
├── 📁 deployment/                       # Prompts về triển khai
│   ├── docker.prompt.md                ✅ Docker Compose, containers, volumes
│   ├── single-server.prompt.md         📝 TODO: All-in-one deployment
│   ├── multi-server.prompt.md          📝 TODO: Microservices architecture
│   └── troubleshoot.prompt.md          📝 TODO: Common issues, debugging
│
├── 📁 frontend/                         # Prompts về React UI
│   ├── components.prompt.md            ✅ React components, props, styling
│   ├── services.prompt.md              📝 TODO: API integration, axios
│   └── state-management.prompt.md      📝 TODO: Hooks, Context, state patterns
│
└── 📁 workflows/                        # Prompts về quy trình
    ├── new-feature.prompt.md           ✅ Add feature workflow, planning
    ├── bug-fix.prompt.md               ✅ Debug process, testing
    ├── code-review.prompt.md           📝 TODO: Review checklist, standards
    └── testing.prompt.md               📝 TODO: Unit, integration, E2E tests
```

**Chú thích**:
- ✅ = Đã hoàn thành
- 📝 = Cần tạo/bổ sung

---

## 📊 Phân loại Prompts theo Chức năng

### 1️⃣ API Endpoints (api/)

#### violations.prompt.md
**Chức năng**: Quản lý violations API
- ✅ GET /violations - List, filter, pagination
- ✅ GET /violations/{id} - Chi tiết violation
- ✅ POST /violations - Tạo mới
- ✅ PUT /violations/{id} - Update status
- ✅ DELETE /violations/{id} - Soft delete
- ✅ Pitfalls: Performance, pagination, validation
- ✅ Examples: Query patterns, responses

#### cameras.prompt.md
**Chức năng**: Quản lý cameras và ROI
- ✅ GET /cameras - List cameras
- ✅ GET /cameras/{id} - Camera details
- ✅ POST /cameras - Add camera
- ✅ PUT /cameras/{id} - Update config
- ✅ PUT /cameras/{id}/roi - Update ROI
- ✅ POST /cameras/{id}/test-stream - Test connectivity
- ✅ Pitfalls: Stream validation, ROI normalization
- ✅ Examples: Create, update ROI

#### streams.prompt.md (TODO)
**Chức năng**: Video streaming
- Checklist: MJPEG endpoints
- Checklist: WebSocket real-time
- Checklist: Frame rate control
- Checklist: Multiple camera streams
- Checklist: Bandwidth optimization

#### detection.prompt.md (TODO)
**Chức năng**: Detection API endpoints
- Checklist: Start/stop detection
- Checklist: Get detection status
- Checklist: Real-time results
- Checklist: Detection configuration

---

### 2️⃣ Database (database/)

#### schema.prompt.md
**Chức năng**: MongoDB schema structure
- ✅ Collection: violations - Fields, indexes, validation
- ✅ Collection: cameras - ROI config, detection config
- ✅ Collection: metadata - Statistics, analytics
- ✅ Pitfalls: Indexing, binary data, validation
- ✅ Examples: Queries, aggregations

#### queries.prompt.md (TODO)
**Chức năng**: Common query patterns
- Checklist: Filter violations by camera
- Checklist: Time range queries
- Checklist: Aggregations by type/hour
- Checklist: Top violating plates
- Checklist: Performance optimization

#### migrations.prompt.md (TODO)
**Chức năng**: Schema updates
- Checklist: Backup strategy
- Checklist: Migration scripts
- Checklist: Rollback plan
- Checklist: Data validation
- Checklist: Zero-downtime migrations

---

### 3️⃣ Detection (detection/)

#### yolo.prompt.md
**Chức năng**: YOLO vehicle detection
- ✅ Model selection (n/s/m/l)
- ✅ Configuration (thresholds, NMS)
- ✅ Preprocessing và inference
- ✅ Performance benchmarks
- ✅ Pitfalls: GPU usage, memory, thresholds
- ✅ Examples: Single frame, batch processing

#### license-plate.prompt.md
**Chức năng**: OCR biển số xe
- ✅ Preprocessing (grayscale, threshold, denoise)
- ✅ Plate localization
- ✅ OCR engine (PaddleOCR)
- ✅ Validation format VN
- ✅ Pitfalls: Preprocessing, confidence, format
- ✅ Examples: Success, low confidence, failed

#### tracking.prompt.md
**Chức năng**: Object tracking
- ✅ DeepSORT configuration
- ✅ Matching algorithm
- ✅ ROI entry/exit tracking
- ✅ Track lifecycle management
- ✅ Pitfalls: IOU threshold, memory, thread safety
- ✅ Examples: Basic tracking, ROI events

#### violations.prompt.md (TODO)
**Chức năng**: Violation detection logic
- Checklist: Red light violation
- Checklist: Stop sign violation
- Checklist: Wrong lane violation
- Checklist: Speed violation
- Checklist: No helmet detection
- Checklist: Rules engine
- Checklist: Evidence collection

---

### 4️⃣ Deployment (deployment/)

#### docker.prompt.md
**Chức năng**: Docker deployment
- ✅ System requirements
- ✅ Pre-deployment checklist
- ✅ Single server deployment steps
- ✅ Multi server deployment
- ✅ Service start order
- ✅ Pitfalls: Ports, volumes, networking
- ✅ Troubleshooting checklist

#### single-server.prompt.md (TODO)
**Chức năng**: All-in-one deployment
- Checklist: Hardware requirements
- Checklist: Installation steps
- Checklist: Configuration files
- Checklist: Start all services
- Checklist: Health checks
- Checklist: Monitoring setup

#### multi-server.prompt.md (TODO)
**Chức năng**: Microservices deployment
- Checklist: Server 1 - MongoDB setup
- Checklist: Server 2 - YOLO service
- Checklist: Server 3 - Backend API
- Checklist: Server 4 - Frontend
- Checklist: Network configuration
- Checklist: Load balancing

#### troubleshoot.prompt.md (TODO)
**Chức năng**: Debug deployment
- Checklist: Container not starting
- Checklist: Service connectivity issues
- Checklist: Performance problems
- Checklist: Data persistence issues
- Checklist: Log analysis
- Checklist: Common errors

---

### 5️⃣ Frontend (frontend/)

#### components.prompt.md
**Chức năng**: React components
- ✅ CameraTile - Live stream display
- ✅ ViolationCard - Violation display
- ✅ RegionEditorModal - ROI editor
- ✅ ViolationList - Paginated list
- ✅ CameraGrid - Multiple cameras
- ✅ Pitfalls: Performance, state, styling
- ✅ Best practices: Props, accessibility

#### services.prompt.md (TODO)
**Chức năng**: API integration layer
- Checklist: Axios configuration
- Checklist: API endpoints mapping
- Checklist: Error handling
- Checklist: Request interceptors
- Checklist: Response transformation
- Checklist: Caching strategy

#### state-management.prompt.md (TODO)
**Chức năng**: State patterns
- Checklist: Local state (useState)
- Checklist: Context API usage
- Checklist: Custom hooks
- Checklist: External state (Zustand)
- Checklist: State synchronization
- Checklist: Performance optimization

---

### 6️⃣ Workflows (workflows/)

#### new-feature.prompt.md
**Chức năng**: Add feature workflow
- ✅ Planning và design
- ✅ Create feature branch
- ✅ Implementation checklist
- ✅ Testing (unit, integration, manual)
- ✅ Documentation updates
- ✅ Code review và merge
- ✅ Pitfalls: Scope creep, no tests
- ✅ Templates: API, Detection, UI

#### bug-fix.prompt.md
**Chức năng**: Debug workflow
- ✅ Reproduce bug
- ✅ Diagnose root cause
- ✅ Implement fix
- ✅ Test thoroughly
- ✅ Document fix
- ✅ Pitfalls: Symptoms vs cause, no regression test
- ✅ Templates: Detection, API, Frontend bugs

#### code-review.prompt.md (TODO)
**Chức năng**: Review checklist
- Checklist: Code style và conventions
- Checklist: Logic correctness
- Checklist: Error handling
- Checklist: Performance considerations
- Checklist: Security issues
- Checklist: Test coverage
- Checklist: Documentation

#### testing.prompt.md (TODO)
**Chức năng**: Testing guidelines
- Checklist: Unit testing (pytest)
- Checklist: Integration testing
- Checklist: E2E testing (Playwright)
- Checklist: Performance testing
- Checklist: Test coverage goals
- Checklist: Mocking strategies
- Checklist: CI/CD integration

---

## 🎯 Mục đích từng Prompt

### Mục đích Core
1. **Tra cứu nhanh**: Agent tìm thông tin trong < 30s
2. **Tránh đọc code**: Không cần đọc source code trừ khi cần thiết
3. **Checklist-driven**: Follow checklist đảm bảo đầy đủ
4. **Pitfalls awareness**: Tránh lỗi thường gặp
5. **Examples-based**: Học từ examples có sẵn

### Format Chuẩn Mỗi Prompt
```yaml
# 🎯 TITLE - PROMPT

## 📋 Metadata
tags: [...]
inputs: [...]
tools: [...]
output_format: ...
complexity: Low|Medium|High

## 🎯 Chức năng
- Giải thích module/feature
- Vị trí trong hệ thống
- Dependencies

## ✅ Checklist
- Các bước cần làm
- Điều kiện check
- Validation rules

## ⚠️ Pitfalls
- Lỗi thường gặp
- Cách tránh

## 📝 Examples
- Use cases thực tế
- Input/output samples

## 🔧 Implementation
- Configuration
- Code patterns

## 🧪 Testing
- Test cases
- Edge cases

## 🔗 Related Prompts
- Links tới prompts liên quan
```

---

## 📈 Roadmap Hoàn thiện

### Phase 1: Core Prompts ✅ (Đã hoàn thành)
- ✅ README.md
- ✅ INDEX.md
- ✅ AI_AGENT_GUIDE.md
- ✅ api/violations.prompt.md
- ✅ api/cameras.prompt.md
- ✅ database/schema.prompt.md
- ✅ detection/yolo.prompt.md
- ✅ detection/license-plate.prompt.md
- ✅ detection/tracking.prompt.md
- ✅ deployment/docker.prompt.md
- ✅ frontend/components.prompt.md
- ✅ workflows/new-feature.prompt.md
- ✅ workflows/bug-fix.prompt.md

### Phase 2: Extended Prompts 📝 (TODO)
- [ ] api/streams.prompt.md
- [ ] api/detection.prompt.md
- [ ] database/queries.prompt.md
- [ ] database/migrations.prompt.md
- [ ] detection/violations.prompt.md
- [ ] deployment/single-server.prompt.md
- [ ] deployment/multi-server.prompt.md
- [ ] deployment/troubleshoot.prompt.md
- [ ] frontend/services.prompt.md
- [ ] frontend/state-management.prompt.md
- [ ] workflows/code-review.prompt.md
- [ ] workflows/testing.prompt.md

### Phase 3: Advanced Topics 🚀 (Future)
- [ ] Performance optimization prompts
- [ ] Security best practices
- [ ] Monitoring và alerting
- [ ] Scaling strategies
- [ ] CI/CD pipelines

---

## 💡 Hướng dẫn Sử dụng

### Cho AI Agent

**Bước 1**: Nhận request từ user
```
User: "Fix bug license plate không đọc được"
```

**Bước 2**: Tra INDEX.md
```
Tags: #license-plate, #bug-fix
Prompts: 
  - detection/license-plate.prompt.md
  - workflows/bug-fix.prompt.md
```

**Bước 3**: Đọc prompts (2 files thay vì cả repo)
```
- Hiểu pipeline OCR
- Hiểu common pitfalls
- Follow bug-fix workflow
```

**Bước 4**: Implement fix
```
- Check preprocessing
- Validate confidence threshold
- Test với examples
- Follow testing checklist
```

### Cho Developer

**Use case 1**: Thêm feature mới
1. Đọc `workflows/new-feature.prompt.md`
2. Đọc prompts của modules liên quan
3. Follow checklist từng bước

**Use case 2**: Review code
1. Đọc `workflows/code-review.prompt.md` (TODO)
2. Check against module-specific checklist
3. Verify examples và patterns

**Use case 3**: Deploy
1. Đọc `deployment/docker.prompt.md`
2. Choose single hoặc multi-server
3. Follow deployment checklist

---

## 📊 Thống kê

### Tổng số Prompts
- **Đã hoàn thành**: 13 prompts
- **TODO**: 12 prompts
- **Tổng cộng**: 25 prompts (planned)

### Coverage by Category
- API: 2/4 (50%)
- Database: 1/3 (33%)
- Detection: 3/4 (75%)
- Deployment: 1/4 (25%)
- Frontend: 1/3 (33%)
- Workflows: 2/4 (50%)

### Estimated Lines
- Mỗi prompt: ~200-300 dòng
- Tổng: ~6,500 dòng documentation
- Time to read 1 prompt: ~5 phút
- Time to read all: ~2 giờ (vs 10+ giờ đọc code)

---

## 🎓 Best Practices

### Khi viết prompts mới
1. ✅ Follow template chuẩn
2. ✅ Include metadata đầy đủ
3. ✅ Add concrete examples
4. ✅ Document pitfalls thực tế
5. ✅ Link related prompts
6. ✅ Keep concise (< 400 dòng)

### Khi update prompts
1. ✅ Update khi code thay đổi
2. ✅ Add new pitfalls discovered
3. ✅ Improve examples
4. ✅ Keep INDEX.md synchronized
5. ✅ Version control important changes

### Khi sử dụng prompts
1. ✅ Đọc metadata trước
2. ✅ Check examples trước khi code
3. ✅ Follow checklist đầy đủ
4. ✅ Review pitfalls section
5. ✅ Test theo test checklist

---

## 🔗 Liên kết Nhanh

### Documentation Core
- [README.md](./README.md) - Giới thiệu commands/
- [INDEX.md](./INDEX.md) - Tra cứu theo tags
- [AI_AGENT_GUIDE.md](./AI_AGENT_GUIDE.md) - Guide cho Agent

### Top Prompts (Most Used)
1. [workflows/bug-fix.prompt.md](./workflows/bug-fix.prompt.md)
2. [detection/violations.prompt.md](./detection/violations.prompt.md) (TODO)
3. [api/violations.prompt.md](./api/violations.prompt.md)
4. [deployment/docker.prompt.md](./deployment/docker.prompt.md)

### Quick Access by Task
- **Fix bugs**: workflows/bug-fix.prompt.md
- **Add features**: workflows/new-feature.prompt.md
- **Deploy**: deployment/docker.prompt.md
- **API work**: api/*.prompt.md
- **Detection work**: detection/*.prompt.md

---

**Cập nhật lần cuối**: 2025-10-28
**Version**: 1.0.0
**Status**: Phase 1 Complete ✅
