# 💾 DATABASE SCHEMA - PROMPT

## 📋 Metadata
```yaml
tags: [database, mongodb, schema, collections]
inputs:
  - collection_name
  - operation_type (read/write/update)
tools:
  - MongoDB
  - PyMongo/Motor
output_format: JSON documents
complexity: Medium
```

---

## 🎯 Database Structure

### Database Name: `traffic_violations`

### Collections Overview:
1. **violations** - Vi phạm giao thông detected
2. **cameras** - Thông tin cameras và ROI config
3. **metadata** - System metadata và statistics

**Vị trí**: MongoDB server (containerized hoặc Atlas)
**Access**: Qua `mongodb_service.py` client

---

## 📊 Collection: violations

### Purpose
Lưu trữ tất cả violations detected từ cameras

### Schema Structure
```
{
  _id: ObjectId
  violation_id: String (unique, indexed)
  camera_id: String (indexed)
  timestamp: DateTime (indexed)
  type: String (enum)
  status: String (enum)
  vehicle: Object
  plate: Object
  evidence: Object
  metadata: Object
  created_at: DateTime
  updated_at: DateTime
}
```

### Field Checklist

#### Required Fields
- [ ] `violation_id` - Format: "VIO_YYYYMMDD_XXXXXX"
- [ ] `camera_id` - Reference tới cameras collection
- [ ] `timestamp` - Thời điểm vi phạm xảy ra
- [ ] `type` - Loại vi phạm
- [ ] `status` - Trạng thái xử lý

#### Vehicle Object
- [ ] `type` - car, truck, motorcycle, bus
- [ ] `bbox` - [x1, y1, x2, y2] coordinates
- [ ] `confidence` - YOLO confidence score
- [ ] `color` - Màu xe (optional)
- [ ] `speed` - Tốc độ (optional)

#### Plate Object
- [ ] `text` - Biển số (format: "29A-12345")
- [ ] `confidence` - OCR confidence score
- [ ] `bbox` - Plate coordinates
- [ ] `province` - Tỉnh/thành phố
- [ ] `verified` - Manual verification status

#### Evidence Object
- [ ] `image_path` - Path tới ảnh vi phạm
- [ ] `video_path` - Path tới video clip (optional)
- [ ] `frame_number` - Frame trong video
- [ ] `thumbnail_path` - Thumbnail cho preview

#### Metadata Object
- [ ] `roi_name` - Tên vùng ROI vi phạm
- [ ] `violation_line` - Line coordinates nếu có
- [ ] `processing_time` - Time từ detect đến save
- [ ] `model_version` - YOLO model version used

### Indexes Checklist
- [ ] `violation_id` - Unique index
- [ ] `camera_id` - Regular index
- [ ] `timestamp` - Regular index (for time range queries)
- [ ] `status` - Regular index
- [ ] `type` - Regular index
- [ ] Compound index: `(camera_id, timestamp)`
- [ ] Compound index: `(status, timestamp)`

### Validation Rules
- [ ] `violation_id` matches pattern: `VIO_[0-9]{8}_[0-9]{6}`
- [ ] `type` in allowed values: ["red_light", "stop_sign", "wrong_lane", "speed_violation", "no_helmet"]
- [ ] `status` in: ["pending", "confirmed", "rejected", "under_review"]
- [ ] `timestamp` is valid DateTime
- [ ] `vehicle.confidence` between 0 and 1
- [ ] `plate.confidence` between 0 and 1

---

## 📊 Collection: cameras

### Purpose
Quản lý thông tin cameras và ROI configurations

### Schema Structure
```
{
  _id: ObjectId
  camera_id: String (unique, indexed)
  name: String
  location: Object
  stream_url: String
  status: String (enum)
  roi_config: Array
  detection_config: Object
  created_at: DateTime
  updated_at: DateTime
  last_active: DateTime
}
```

### Field Checklist

#### Basic Info
- [ ] `camera_id` - Format: "CAM001", "CAM002"
- [ ] `name` - Descriptive name (e.g., "Ngã tư Láng Hạ")
- [ ] `status` - "active", "inactive", "maintenance"
- [ ] `stream_url` - RTSP or HTTP stream URL

#### Location Object
- [ ] `address` - Địa chỉ cụ thể
- [ ] `city` - Thành phố
- [ ] `district` - Quận/huyện
- [ ] `coordinates` - GPS [lat, lng]

#### ROI Config Array
Mỗi ROI object:
- [ ] `roi_id` - Unique ID trong camera
- [ ] `name` - Tên vùng (e.g., "Stop line", "Crosswalk")
- [ ] `type` - "line", "polygon", "zone"
- [ ] `coordinates` - Array of points
- [ ] `violation_types` - Các loại vi phạm detect trong ROI
- [ ] `enabled` - true/false

#### Detection Config Object
- [ ] `confidence_threshold` - YOLO threshold
- [ ] `plate_confidence_threshold` - OCR threshold
- [ ] `tracking_enabled` - true/false
- [ ] `frame_skip` - Process every N frames
- [ ] `resolution` - Width x height

### Indexes Checklist
- [ ] `camera_id` - Unique index
- [ ] `status` - Regular index
- [ ] `location.city` - Regular index

---

## 📊 Collection: metadata

### Purpose
Lưu system statistics và analytics

### Schema Structure
```
{
  _id: ObjectId
  date: Date (indexed)
  camera_id: String (indexed)
  stats: Object
  created_at: DateTime
}
```

### Stats Object Checklist
- [ ] `total_detections` - Tổng số detections
- [ ] `total_violations` - Tổng số violations
- [ ] `by_type` - Breakdown theo violation type
- [ ] `by_hour` - Breakdown theo giờ trong ngày
- [ ] `avg_processing_time` - Average time per frame
- [ ] `uptime_minutes` - Số phút camera active

### Indexes
- [ ] Compound: `(date, camera_id)` - Unique
- [ ] `date` - For time range queries

---

## ✅ Common Queries Checklist

### Get Violations
- [ ] Filter by camera_id
- [ ] Filter by date range (start_time, end_time)
- [ ] Filter by type
- [ ] Filter by status
- [ ] Pagination (skip, limit)
- [ ] Sort by timestamp descending

### Aggregations
- [ ] Count violations per camera
- [ ] Count violations per type
- [ ] Count violations per hour
- [ ] Average confidence scores
- [ ] Top violating plates

### Updates
- [ ] Update violation status
- [ ] Update camera ROI config
- [ ] Soft delete violations (set deleted=true)

---

## ⚠️ Pitfalls

### 1. Không index các fields query thường xuyên
❌ **Sai**: Query camera_id mà không có index
- Kết quả: Slow queries, full collection scan

✅ **Đúng**: Index tất cả filter fields

### 2. Lưu binary data trong MongoDB
❌ **Sai**: Lưu images as binary trong violations
- Kết quả: Database quá lớn, slow queries

✅ **Đúng**: Lưu file paths, images trên filesystem

### 3. Không validate data trước khi insert
❌ **Sai**: Insert invalid data → corrupt database
- Kết quả: Queries fail, data inconsistent

✅ **Đúng**: Validate với Pydantic models

### 4. Hardcode connection strings
❌ **Sai**: Connection string trong code
- Kết quả: Security risk, không flexible

✅ **Đúng**: Dùng environment variables

### 5. Không handle ObjectId correctly
❌ **Sai**: Compare ObjectId as string
- Kết quả: Queries fail

✅ **Đúng**: Convert properly: `ObjectId(id_string)`

---

## 🔧 Implementation Checklist

### Setup Database
- [ ] Create database: `traffic_violations`
- [ ] Create collections với validation schemas
- [ ] Create indexes
- [ ] Set up user authentication
- [ ] Configure backup strategy

### CRUD Operations
- [ ] Create: `insert_one()`, `insert_many()`
- [ ] Read: `find()`, `find_one()`, `aggregate()`
- [ ] Update: `update_one()`, `update_many()`
- [ ] Delete: `delete_one()` (hoặc soft delete)

### Connection Management
- [ ] Connection pooling configured
- [ ] Retry logic cho network errors
- [ ] Timeout settings
- [ ] Close connections properly

### Data Migration
- [ ] Backup before migration
- [ ] Test migration script
- [ ] Run migration
- [ ] Verify data integrity
- [ ] Rollback plan ready

---

## 📝 Query Examples

### Example 1: Get pending violations for camera
```
Inputs:
  - camera_id: "CAM001"
  - status: "pending"
  - limit: 20

Expected output:
  Array of 20 violation documents
```

### Example 2: Aggregate violations by type
```
Inputs:
  - camera_id: "CAM001" (optional)
  - start_date: "2025-10-01"
  - end_date: "2025-10-31"

Expected output:
  {
    "red_light": 45,
    "stop_sign": 12,
    "speed_violation": 8
  }
```

### Example 3: Update camera ROI
```
Inputs:
  - camera_id: "CAM001"
  - roi_config: [new ROI array]

Expected result:
  Updated camera document
```

---

## 🧪 Testing Checklist

### Data Validation
- [ ] Invalid violation_id format → Reject
- [ ] Invalid timestamp → Reject
- [ ] Missing required fields → Reject
- [ ] Invalid enum values → Reject

### Query Performance
- [ ] Query 1000 violations < 100ms
- [ ] Aggregation queries < 500ms
- [ ] Index coverage > 95%

### Data Integrity
- [ ] Foreign key references valid (camera_id exists)
- [ ] No duplicate violation_ids
- [ ] Timestamps trong valid range

---

## 🔗 Related Prompts

- `api/violations.prompt.md` - API sử dụng violations collection
- `database/queries.prompt.md` - Common query patterns
- `database/migrations.prompt.md` - Schema migration guide
- `deployment/docker.prompt.md` - MongoDB deployment
