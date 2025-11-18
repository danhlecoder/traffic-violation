# 🚨 VIOLATIONS API - PROMPT

## 📋 Metadata
```yaml
tags: [api, violations, crud, rest]
inputs: 
  - camera_id (string)
  - time_range (datetime)
  - violation_type (string)
  - status (pending|confirmed|rejected)
tools:
  - FastAPI
  - Pydantic models
  - MongoDB client
output_format: JSON với pagination
complexity: Medium
```

---

## 🎯 Chức năng

### Endpoint: `/api/v1/violations`
**Mục đích**: Quản lý và truy vấn violations (vi phạm giao thông)

**Vị trí file**: `backend/api/v1/violations.py`

**Dependencies**:
- `backend/core/violations/repository.py` - Database operations
- `backend/core/violations/creator.py` - Tạo violation records
- `backend/clients/mongodb_service.py` - MongoDB client

---

## ✅ Checklist API Violations

### GET /api/v1/violations
- [ ] Hỗ trợ filter theo camera_id
- [ ] Hỗ trợ filter theo time range (start_time, end_time)
- [ ] Hỗ trợ filter theo violation_type
- [ ] Hỗ trợ filter theo status
- [ ] Pagination (page, limit)
- [ ] Sort theo timestamp (mới nhất trước)
- [ ] Response có total_count
- [ ] Response có metadata (camera info)

### GET /api/v1/violations/{violation_id}
- [ ] Validate violation_id format
- [ ] Return 404 nếu không tồn tại
- [ ] Include đầy đủ metadata (camera, vehicle, plate)
- [ ] Include evidence images (URLs)

### POST /api/v1/violations
- [ ] Validate required fields
- [ ] Auto-generate violation_id
- [ ] Save evidence images
- [ ] Set default status = "pending"
- [ ] Set timestamp = current time
- [ ] Return created violation với status 201

### PUT /api/v1/violations/{violation_id}
- [ ] Chỉ cho phép update status
- [ ] Validate status values
- [ ] Log ai update, khi nào
- [ ] Không cho phép update sau khi confirmed

### DELETE /api/v1/violations/{violation_id}
- [ ] Soft delete (set deleted=true)
- [ ] Không xóa physical data
- [ ] Xóa cả evidence images
- [ ] Require admin permission

---

## ⚠️ Pitfalls - Tránh những lỗi này

### 1. Performance Issues
❌ **Sai**: Query toàn bộ violations rồi filter trong Python
```
Đừng làm: get_all() -> filter trong memory
```

✅ **Đúng**: Filter ngay trong MongoDB query
```
Làm đúng: Dùng MongoDB aggregation pipeline
```

### 2. Pagination
❌ **Sai**: Không có limit → timeout khi có hàng ngàn records

✅ **Đúng**: Default limit=50, max limit=100

### 3. Image URLs
❌ **Sai**: Trả về base64 image trong response → response quá lớn

✅ **Đúng**: Trả về URL path, client fetch riêng

### 4. Time Range Filter
❌ **Sai**: So sánh string timestamps

✅ **Đúng**: Convert sang datetime object, dùng MongoDB $gte, $lte

### 5. Validation
❌ **Sai**: Không validate camera_id → query lỗi

✅ **Đúng**: Check camera exists trước khi query

---

## 📝 Input/Output Examples

### Example 1: Get violations với filter
**Request**:
```
GET /api/v1/violations?camera_id=CAM001&status=pending&page=1&limit=20
```

**Response**:
```
{
  "violations": [...],
  "total": 156,
  "page": 1,
  "limit": 20,
  "has_more": true
}
```

### Example 2: Get violation detail
**Request**:
```
GET /api/v1/violations/VIO_20251028_001
```

**Response**:
```
{
  "violation_id": "VIO_20251028_001",
  "camera_id": "CAM001",
  "type": "red_light",
  "timestamp": "2025-10-28T15:30:45Z",
  "vehicle": {
    "type": "car",
    "color": "red",
    "plate": "29A-12345"
  },
  "evidence": {
    "image_url": "/evidence/VIO_20251028_001.jpg",
    "video_url": "/evidence/VIO_20251028_001.mp4"
  },
  "status": "pending"
}
```

### Example 3: Update status
**Request**:
```
PUT /api/v1/violations/VIO_20251028_001
{
  "status": "confirmed"
}
```

---

## 🔧 Implementation Checklist

Khi implement violations API:

### 1. Repository Layer
- [ ] Tạo ViolationRepository class
- [ ] Implement CRUD methods
- [ ] Dùng MongoDB aggregation cho complex queries
- [ ] Handle errors gracefully

### 2. Validation
- [ ] Dùng Pydantic models cho request/response
- [ ] Validate enum values (status, type)
- [ ] Validate datetime formats
- [ ] Validate camera_id exists

### 3. Performance
- [ ] Index MongoDB fields (camera_id, timestamp, status)
- [ ] Limit response size
- [ ] Cache frequently accessed data
- [ ] Async operations nếu có thể

### 4. Security
- [ ] Authentication required
- [ ] Authorization check (role-based)
- [ ] Rate limiting
- [ ] Input sanitization

### 5. Error Handling
- [ ] Return proper HTTP status codes
- [ ] Clear error messages
- [ ] Log errors cho debugging
- [ ] Don't expose internal details

---

## 🧪 Testing Checklist

- [ ] Test pagination works
- [ ] Test filters work independently
- [ ] Test filters work combined
- [ ] Test invalid camera_id → 400
- [ ] Test invalid violation_id → 404
- [ ] Test invalid status → 400
- [ ] Test empty results → empty array
- [ ] Test performance với 10000+ records

---

## 🔗 Related Prompts

- `database/schema.prompt.md` - Violations schema structure
- `detection/violations.prompt.md` - Violation detection logic
- `frontend/components.prompt.md` - UI components consume API
- `workflows/testing.prompt.md` - Testing guidelines
