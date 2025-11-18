# ✨ NEW FEATURE WORKFLOW - PROMPT

## 📋 Metadata
```yaml
tags: [workflow, development, feature, planning]
inputs:
  - feature_description
  - requirements
  - acceptance_criteria
tools:
  - Git
  - IDE
  - Testing framework
output_format: Implemented feature + tests + docs
complexity: Variable
```

---

## 🎯 Quy trình Thêm Feature Mới

### 6 Bước Chính
1. **Plan** - Lập kế hoạch và design
2. **Branch** - Tạo feature branch
3. **Implement** - Code feature
4. **Test** - Viết và chạy tests
5. **Document** - Update docs
6. **Review** - Code review và merge

---

## ✅ Checklist Bước 1: PLANNING

### Hiểu Requirements
- [ ] Đọc kỹ feature request
- [ ] Clarify unclear requirements
- [ ] Identify acceptance criteria
- [ ] List constraints và limitations
- [ ] Estimate effort (small/medium/large)

### Technical Design
- [ ] Xác định modules cần thay đổi
- [ ] List files cần tạo/sửa
- [ ] Design API changes (nếu có)
- [ ] Design database changes (nếu có)
- [ ] Identify dependencies
- [ ] Consider backwards compatibility

### Check Existing Code
- [ ] Search codebase cho similar features
- [ ] Review related prompts trong `commands/`
- [ ] Check có library/tool nào hỗ trợ không
- [ ] Identify reusable components

### Risk Assessment
- [ ] Breaking changes?
- [ ] Performance impact?
- [ ] Security implications?
- [ ] Data migration needed?

---

## ✅ Checklist Bước 2: BRANCHING

### Create Feature Branch
- [ ] Pull latest từ dev/main: `git pull origin dev`
- [ ] Create branch: `git checkout -b feat/feature-name`
- [ ] Branch naming convention: `feat/`, `feature/`
- [ ] Descriptive name (e.g., `feat/add-speed-detection`)

### Setup Environment
- [ ] Install new dependencies (nếu cần)
- [ ] Update config files
- [ ] Create .env variables (nếu cần)
- [ ] Verify environment works

---

## ✅ Checklist Bước 3: IMPLEMENTATION

### Follow Best Practices
- [ ] Follow existing code style
- [ ] Use design patterns from codebase
- [ ] Keep functions small và focused
- [ ] DRY principle (Don't Repeat Yourself)
- [ ] SOLID principles

### Code Organization
- [ ] Files trong đúng directories
- [ ] Clear naming conventions
- [ ] Proper imports
- [ ] Proper error handling
- [ ] Logging statements

### Incremental Development
- [ ] Start với smallest working version
- [ ] Commit frequently với clear messages
- [ ] Test incrementally
- [ ] Refactor as you go

### Frontend Features
- [ ] Create/update components
- [ ] Update routing (nếu cần)
- [ ] Update state management
- [ ] Responsive design
- [ ] Accessibility (a11y)

### Backend Features
- [ ] Create/update API endpoints
- [ ] Add request/response models
- [ ] Implement business logic
- [ ] Add validation
- [ ] Error handling

### Database Changes
- [ ] Update schema
- [ ] Create migration scripts
- [ ] Update indexes
- [ ] Test with sample data

---

## ✅ Checklist Bước 4: TESTING

### Unit Tests
- [ ] Test individual functions
- [ ] Test edge cases
- [ ] Test error conditions
- [ ] Mock external dependencies
- [ ] Aim for >80% coverage

### Integration Tests
- [ ] Test API endpoints end-to-end
- [ ] Test database operations
- [ ] Test service interactions
- [ ] Test với real-like data

### Manual Testing
- [ ] Test trên local environment
- [ ] Test all user flows
- [ ] Test edge cases
- [ ] Cross-browser testing (frontend)
- [ ] Mobile responsive (frontend)

### Performance Testing
- [ ] Load testing (nếu cần)
- [ ] Check memory usage
- [ ] Check response times
- [ ] Optimize bottlenecks

---

## ✅ Checklist Bước 5: DOCUMENTATION

### Code Documentation
- [ ] Add docstrings to functions
- [ ] Add inline comments for complex logic
- [ ] Update type hints
- [ ] Document assumptions

### API Documentation
- [ ] Update OpenAPI/Swagger docs
- [ ] Add example requests/responses
- [ ] Document error codes
- [ ] Update Postman collection

### User Documentation
- [ ] Update README nếu cần
- [ ] Update user guides
- [ ] Add screenshots/GIFs
- [ ] Update FAQs

### Developer Documentation
- [ ] Update architecture docs
- [ ] Add to CHANGELOG
- [ ] Update prompts trong `commands/` (nếu cần)
- [ ] Document configuration options

---

## ✅ Checklist Bước 6: REVIEW & MERGE

### Self Review
- [ ] Review own code trước khi PR
- [ ] Check code style
- [ ] Remove debug code
- [ ] Remove commented code
- [ ] Check for sensitive data (API keys, etc)

### Create Pull Request
- [ ] Descriptive PR title
- [ ] Clear description
- [ ] Link to issue/ticket
- [ ] Screenshots/GIFs (UI changes)
- [ ] Checklist of changes
- [ ] Mark breaking changes

### Code Review
- [ ] Address reviewer comments
- [ ] Update code based on feedback
- [ ] Respond to questions
- [ ] Re-request review after changes

### Pre-Merge Checklist
- [ ] All tests pass
- [ ] No merge conflicts
- [ ] CI/CD pipeline green
- [ ] Approved by reviewer(s)
- [ ] Documentation updated

### Merge
- [ ] Squash commits (nếu cần)
- [ ] Clear merge commit message
- [ ] Delete feature branch after merge
- [ ] Verify deployed correctly

---

## ⚠️ Common Pitfalls

### 1. Scope Creep
❌ **Sai**: Thêm nhiều features không liên quan vào 1 PR
✅ **Đúng**: 1 PR = 1 feature, focused

### 2. Không viết tests
❌ **Sai**: "Sẽ viết tests sau"
✅ **Đúng**: Write tests cùng lúc với code

### 3. Hardcode values
❌ **Sai**: Hardcode URLs, thresholds, configs
✅ **Đúng**: Dùng config files hoặc environment variables

### 4. Không xử lý errors
❌ **Sai**: Happy path only
✅ **Đúng**: Handle errors gracefully

### 5. Breaking backwards compatibility
❌ **Sai**: Change API mà không versioning
✅ **Đúng**: Version APIs hoặc deprecate gradually

### 6. Không update documentation
❌ **Sai**: Code có, docs không
✅ **Đúng**: Code và docs đồng bộ

---

## 📝 Feature Templates

### Template 1: API Endpoint

**Feature**: Add endpoint để filter violations by speed

**Files to modify**:
- `backend/api/v1/violations.py` - Add endpoint
- `backend/core/violations/repository.py` - Add query
- `frontend/src/services/violations.ts` - Add client method

**Checklist**:
- [ ] Add `speed_min`, `speed_max` query params
- [ ] Validate params
- [ ] Update MongoDB query
- [ ] Add unit tests
- [ ] Update API docs
- [ ] Test manually

### Template 2: Detection Feature

**Feature**: Detect xe không đội mũ bảo hiểm

**Files to create/modify**:
- `backend/core/detection/helmet_detector.py` - New detector
- `backend/core/violations/creator.py` - Add violation type
- `backend/config/server.yaml` - Add configs
- `database schema` - Add violation type

**Checklist**:
- [ ] Train/download helmet detection model
- [ ] Implement detector class
- [ ] Integrate vào pipeline
- [ ] Add "no_helmet" violation type
- [ ] Update database schema
- [ ] Add tests
- [ ] Update frontend UI

### Template 3: UI Component

**Feature**: Dashboard widget hiển thị violations by hour

**Files to create/modify**:
- `frontend/src/components/ViolationsByHourChart.tsx` - New component
- `frontend/src/pages/Dashboard.tsx` - Add widget
- `frontend/src/services/analytics.ts` - API call

**Checklist**:
- [ ] Create chart component (use Chart.js/Recharts)
- [ ] Fetch data từ API
- [ ] Handle loading state
- [ ] Handle errors
- [ ] Responsive design
- [ ] Add to dashboard layout
- [ ] Test on different screen sizes

---

## 🧪 Testing Scenarios

### Functional Testing
- [ ] Feature works as specified
- [ ] All acceptance criteria met
- [ ] User flows complete successfully

### Edge Cases
- [ ] Empty data
- [ ] Very large data
- [ ] Invalid inputs
- [ ] Concurrent operations
- [ ] Network failures

### Integration
- [ ] Works with existing features
- [ ] Doesn't break existing functionality
- [ ] APIs communicate correctly

### Non-Functional
- [ ] Performance acceptable
- [ ] Security không bị compromise
- [ ] Accessibility standards met

---

## 📊 Metrics to Track

### Code Quality
- **Lines of Code**: Giữ reasonable
- **Cyclomatic Complexity**: < 10 per function
- **Test Coverage**: > 80%
- **Code Duplication**: < 5%

### Performance
- **API Response Time**: < 1s
- **Page Load Time**: < 3s
- **Memory Usage**: Không tăng đáng kể

### Process
- **Time to Implement**: Actual vs Estimate
- **Number of Revisions**: PR iterations
- **Time to Review**: Review turnaround

---

## 🔗 Related Prompts

- `workflows/bug-fix.prompt.md` - Fix issues in feature
- `workflows/code-review.prompt.md` - Review checklist
- `workflows/testing.prompt.md` - Testing guidelines
- Specific module prompts: `api/`, `detection/`, `frontend/`, etc.
