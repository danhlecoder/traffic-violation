# 🐛 BUG FIX WORKFLOW - PROMPT

## 📋 Metadata
```yaml
tags: [workflow, debugging, bug-fix, troubleshooting]
inputs:
  - bug_description
  - error_logs
  - steps_to_reproduce
tools:
  - Debugger
  - Logging
  - Git
  - Testing framework
output_format: Fixed code + test case
complexity: Variable
```

---

## 🎯 Quy trình Fix Bug

### 5 Bước Cơ Bản
1. **Reproduce** - Tái hiện lỗi
2. **Diagnose** - Tìm root cause
3. **Fix** - Sửa code
4. **Test** - Verify fix works
5. **Document** - Ghi chú và commit

---

## ✅ Checklist Bước 1: REPRODUCE

### Thu thập thông tin
- [ ] Bug description rõ ràng
- [ ] Steps to reproduce
- [ ] Expected vs Actual behavior
- [ ] Environment (OS, Python version, dependencies)
- [ ] Error logs/stack trace
- [ ] Screenshots/videos nếu UI bug

### Tái hiện lỗi
- [ ] Follow exact steps
- [ ] Reproduce on local environment
- [ ] Reproduce on staging/production (nếu cần)
- [ ] Xác nhận bug vẫn tồn tại
- [ ] Note các conditions trigger bug

### Phân loại bug
- [ ] **Critical**: Crash, data loss, security
- [ ] **High**: Core functionality broken
- [ ] **Medium**: Feature không hoạt động đúng
- [ ] **Low**: UI glitch, typo
- [ ] **Enhancement**: Không phải bug, là feature request

---

## ✅ Checklist Bước 2: DIAGNOSE

### Check logs
- [ ] Backend logs: `backend/logs/app.log`
- [ ] Container logs: `docker logs <container>`
- [ ] Browser console (frontend bugs)
- [ ] MongoDB logs (database issues)
- [ ] YOLO service logs (detection issues)

### Narrow down scope
- [ ] Xác định module bị lỗi (API, Detection, Frontend, Database)
- [ ] Xác định file/function cụ thể
- [ ] Check git history: Lỗi này từ commit nào?
- [ ] Check related issues: Có ai report tương tự?

### Debug strategies
- [ ] **Frontend bug**: Chrome DevTools, React DevTools
- [ ] **API bug**: Postman, curl, FastAPI docs
- [ ] **Detection bug**: Print intermediate results, visualize
- [ ] **Database bug**: MongoDB Compass, check queries
- [ ] **Performance bug**: Profiling, timing logs

### Find root cause
- [ ] Đừng fix symptoms, tìm root cause
- [ ] Trace code execution flow
- [ ] Check assumptions (type, null values, edge cases)
- [ ] Review recent changes
- [ ] Check dependencies versions

---

## ✅ Checklist Bước 3: FIX

### Trước khi sửa
- [ ] Create new branch: `git checkout -b fix/bug-description`
- [ ] Write failing test case first (TDD)
- [ ] Backup current state nếu cần

### Implement fix
- [ ] Sửa minimal code cần thiết
- [ ] Không refactor khi đang fix bug (làm riêng)
- [ ] Follow coding standards
- [ ] Add error handling nếu thiếu
- [ ] Add validation nếu cần

### Review fix
- [ ] Code solves root cause, không chỉ symptoms
- [ ] Không introduce new bugs
- [ ] Không break existing features
- [ ] Performance acceptable
- [ ] Code readable và maintainable

---

## ✅ Checklist Bước 4: TEST

### Unit tests
- [ ] Test case cho bug đã fix
- [ ] Test edge cases related
- [ ] All existing tests pass
- [ ] Coverage không giảm

### Integration tests
- [ ] Test với real data
- [ ] Test với các services khác
- [ ] Test trên môi trường giống production

### Manual testing
- [ ] Reproduce bug → Verify fixed
- [ ] Test related features
- [ ] Test edge cases manually
- [ ] Test trên different browsers/devices (UI bugs)

### Regression testing
- [ ] Run full test suite
- [ ] Check không break existing functionality
- [ ] Performance benchmarks

---

## ✅ Checklist Bước 5: DOCUMENT

### Code comments
- [ ] Add comment giải thích fix (nếu không obvious)
- [ ] Document workarounds nếu có
- [ ] Note potential issues

### Commit message
- [ ] Format: `fix(module): description`
- [ ] Ví dụ: `fix(detection): resolve null pointer in plate OCR`
- [ ] Include issue number nếu có: `fix(api): #123 - handle empty camera list`
- [ ] Mô tả root cause và solution

### Update documentation
- [ ] Update README nếu cần
- [ ] Update API docs
- [ ] Update deployment guide
- [ ] Add to CHANGELOG

### Create PR
- [ ] Descriptive PR title
- [ ] Link to issue/bug report
- [ ] Explain root cause
- [ ] Explain solution
- [ ] Screenshots before/after
- [ ] Test results

---

## ⚠️ Common Pitfalls

### 1. Fixing symptoms thay vì root cause
❌ **Sai**: Frontend crash → Thêm try/catch bao quanh
- Vẫn có bug, chỉ hide error

✅ **Đúng**: Tìm tại sao crash → Fix data validation

### 2. Không reproduce được bug
❌ **Sai**: Guess và fix luôn
- Có thể fix sai, introduce new bugs

✅ **Đúng**: Chắc chắn reproduce được trước khi fix

### 3. Fix quá nhiều thứ cùng lúc
❌ **Sai**: Fix bug + refactor + add feature
- PR khó review, rủi ro cao

✅ **Đúng**: 1 PR = 1 bug fix, focused

### 4. Không viết test
❌ **Sai**: Fix xong, không test → Bug xuất hiện lại
- Regression bugs

✅ **Đúng**: Write test case, đảm bảo không bị lại

### 5. Hardcode fix
❌ **Sai**: `if (id == 'CAM001') { ... }` để fix 1 trường hợp
- Không scale, technical debt

✅ **Đúng**: Fix general case

### 6. Không check side effects
❌ **Sai**: Fix bug A → Break feature B
- Tạo bug mới

✅ **Đúng**: Full regression testing

---

## 📝 Bug Fix Templates

### Template 1: Detection Bug
**Bug**: YOLO không detect xe tải

**Reproduce**:
1. Start backend
2. Point camera tới xe tải
3. Check API response → empty detections

**Diagnosis**:
- Check YOLO logs → confidence threshold quá cao
- Default threshold = 0.8, xe tải confidence = 0.6

**Fix**:
- Lower threshold xuống 0.5 trong config
- Add vehicle type specific thresholds

**Test**:
- Xe tải detected ✓
- Xe con vẫn detected ✓
- Xe máy vẫn detected ✓

### Template 2: API Bug
**Bug**: GET /violations timeout với camera có nhiều violations

**Reproduce**:
1. Camera CAM001 có 10,000 violations
2. GET /violations?camera_id=CAM001
3. Response timeout sau 30s

**Diagnosis**:
- Query không có pagination
- Load toàn bộ 10,000 records vào memory
- Serialize JSON quá lâu

**Fix**:
- Add pagination (default limit=50)
- Add index trên camera_id field
- Optimize query với MongoDB aggregation

**Test**:
- Response time < 1s ✓
- Pagination works ✓
- Data correct ✓

### Template 3: Frontend Bug
**Bug**: Camera stream không hiển thị trên Safari

**Reproduce**:
1. Open app trên Safari
2. Navigate to Live Monitor
3. Streams không load

**Diagnosis**:
- Check console → CORS error
- Safari strict về CORS
- Backend missing headers

**Fix**:
- Add CORS headers: `Access-Control-Allow-Origin`
- Configure FastAPI CORS middleware
- Handle preflight OPTIONS requests

**Test**:
- Works on Safari ✓
- Still works on Chrome/Firefox ✓
- Mobile Safari works ✓

---

## 🔧 Debug Tools Checklist

### Logging
- [ ] Add strategic log points
- [ ] Log inputs, outputs, intermediate values
- [ ] Use log levels appropriately (DEBUG, INFO, ERROR)
- [ ] Don't log sensitive data

### Debugging
- [ ] Use IDE debugger (breakpoints)
- [ ] Use Python debugger: `import pdb; pdb.set_trace()`
- [ ] Use browser DevTools
- [ ] Use Postman for API debugging

### Profiling (Performance bugs)
- [ ] Python: cProfile, line_profiler
- [ ] Monitor memory: memory_profiler
- [ ] Database: MongoDB explain plans
- [ ] Frontend: Chrome Performance tab

### Monitoring
- [ ] Check metrics dashboards
- [ ] Check error tracking (Sentry)
- [ ] Check server resources
- [ ] Check network traffic

---

## 🧪 Testing Scenarios

### Edge Cases to Test
- [ ] Empty input / Null values
- [ ] Very large input (10,000+ items)
- [ ] Special characters trong strings
- [ ] Concurrent requests
- [ ] Network errors / Timeouts
- [ ] Database connection lost
- [ ] Disk full
- [ ] Out of memory

### Error Handling
- [ ] Graceful degradation
- [ ] User-friendly error messages
- [ ] Proper HTTP status codes
- [ ] Logging errors cho debugging
- [ ] Rollback on failure

---

## 📊 Bug Tracking

### Information to Record
- [ ] Bug ID / Ticket number
- [ ] Severity / Priority
- [ ] Date reported / Date fixed
- [ ] Reporter / Assignee
- [ ] Component affected
- [ ] Root cause
- [ ] Solution implemented
- [ ] Time spent

### Metrics
- **MTTD** (Mean Time To Detect): Bao lâu phát hiện bug
- **MTTR** (Mean Time To Resolve): Bao lâu fix xong
- **Bug Density**: Số bugs / 1000 lines of code
- **Reopen Rate**: % bugs bị reopen

---

## 🔗 Related Prompts

- `workflows/testing.prompt.md` - Testing guidelines
- `workflows/code-review.prompt.md` - Code review checklist
- `deployment/troubleshoot.prompt.md` - Deployment debugging
- Specific module prompts cho details (api/, detection/, etc)
