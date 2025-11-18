# 📹 CAMERAS API - PROMPT

## 📋 Metadata
```yaml
tags: [api, cameras, crud, roi, configuration]
inputs:
  - camera_id (string)
  - stream_url (string)
  - roi_config (array of polygons/lines)
tools:
  - FastAPI
  - Pydantic models
  - MongoDB client
output_format: JSON camera objects
complexity: Medium
```

---

## 🎯 Chức năng

### Endpoint: `/api/v1/cameras`
**Mục đích**: Quản lý cameras và ROI configurations

**Vị trí file**: `backend/api/v1/cameras.py`

**Dependencies**:
- `backend/clients/mongodb_service.py` - Database operations
- `backend/utils/camera.py` - Camera utilities
- `backend/config/server.yaml` - Default configs

---

## ✅ Checklist API Endpoints

### GET /api/v1/cameras
**Chức năng**: List tất cả cameras

**Filters**:
- [ ] `status` - active/inactive/maintenance
- [ ] `city` - Filter theo thành phố
- [ ] `district` - Filter theo quận

**Response**:
- [ ] Array of camera objects
- [ ] Include ROI configs
- [ ] Include status
- [ ] Total count

**Checklist**:
- [ ] Return only active cameras by default
- [ ] Pagination (nếu nhiều cameras)
- [ ] Sort theo camera_id

---

### GET /api/v1/cameras/{camera_id}
**Chức năng**: Get camera details

**Response Fields**:
- [ ] `camera_id`
- [ ] `name`
- [ ] `location` (address, coordinates)
- [ ] `stream_url`
- [ ] `status`
- [ ] `roi_config` (array of ROIs)
- [ ] `detection_config`
- [ ] `created_at`, `updated_at`
- [ ] `last_active` timestamp

**Error Handling**:
- [ ] 404 nếu camera không tồn tại
- [ ] Validate camera_id format

---

### POST /api/v1/cameras
**Chức năng**: Add new camera

**Required Fields**:
- [ ] `camera_id` - Unique identifier
- [ ] `name` - Descriptive name
- [ ] `stream_url` - RTSP/HTTP URL
- [ ] `location` - Address object

**Optional Fields**:
- [ ] `roi_config` - Can be set later
- [ ] `detection_config` - Use defaults
- [ ] `status` - Default: active

**Validation**:
- [ ] camera_id unique
- [ ] stream_url valid format
- [ ] Test stream connectivity
- [ ] Validate location coordinates

**Response**:
- [ ] 201 Created
- [ ] Return created camera object

---

### PUT /api/v1/cameras/{camera_id}
**Chức năng**: Update camera config

**Allowed Updates**:
- [ ] `name`
- [ ] `location`
- [ ] `stream_url`
- [ ] `roi_config`
- [ ] `detection_config`
- [ ] `status`

**Restricted**:
- [ ] Không cho update `camera_id`
- [ ] Không cho update `created_at`

**Validation**:
- [ ] Validate stream_url nếu thay đổi
- [ ] Validate ROI format
- [ ] Check camera exists

---

### DELETE /api/v1/cameras/{camera_id}
**Chức năng**: Delete camera

**Behavior**:
- [ ] Soft delete (set status=inactive)
- [ ] Stop active streams
- [ ] Keep violation history
- [ ] Don't delete physical data

**Permissions**:
- [ ] Require admin role

---

### PUT /api/v1/cameras/{camera_id}/roi
**Chức năng**: Update ROI configuration

**Input**:
- [ ] `roi_config` - Array of ROI objects

**ROI Object Structure**:
```
{
  "roi_id": "roi_1",
  "name": "Stop Line",
  "type": "line|polygon|zone",
  "coordinates": [[x1,y1], [x2,y2], ...],
  "violation_types": ["red_light", "stop_sign"],
  "enabled": true
}
```

**Validation**:
- [ ] Coordinates trong valid range (0-1 normalized)
- [ ] Type hợp lệ
- [ ] Violation types valid
- [ ] Minimum 2 points (line), 3 points (polygon)

---

### POST /api/v1/cameras/{camera_id}/test-stream
**Chức năng**: Test camera stream connectivity

**Process**:
- [ ] Try connect to stream_url
- [ ] Capture 1 frame
- [ ] Validate frame format
- [ ] Return connection status

**Response**:
```
{
  "status": "success|failed",
  "latency_ms": 125,
  "resolution": "1920x1080",
  "fps": 30,
  "error": null
}
```

---

## ⚠️ Pitfalls - Tránh những lỗi này

### 1. Không validate stream URL
❌ **Sai**: Accept bất kỳ URL nào
- Kết quả: Camera không connect được

✅ **Đúng**: Test connection trước khi save

### 2. ROI coordinates hardcoded pixels
❌ **Sai**: Coordinates theo resolution cụ thể
- Kết quả: Sai khi resolution thay đổi

✅ **Đúng**: Normalize coordinates (0-1 range)

### 3. Không handle camera offline
❌ **Sai**: Assume camera luôn online
- Kết quả: Errors khi query

✅ **Đúng**: Check status, handle gracefully

### 4. Update ROI không validate
❌ **Sai**: Accept invalid polygon
- Kết quả: Detection logic fails

✅ **Đúng**: Validate coordinates, type, minimum points

### 5. Expose sensitive stream URLs
❌ **Sai**: Return full RTSP URL với credentials
- Kết quả: Security risk

✅ **Đúng**: Mask credentials hoặc proxy stream

---

## 📝 Input/Output Examples

### Example 1: Create Camera
**Request**:
```
POST /api/v1/cameras
{
  "camera_id": "CAM001",
  "name": "Ngã tư Láng Hạ",
  "stream_url": "rtsp://admin:pass@192.168.1.100/stream",
  "location": {
    "address": "Láng Hạ, Đống Đa",
    "city": "Hà Nội",
    "coordinates": [21.0168, 105.8163]
  }
}
```

**Response** (201):
```
{
  "camera_id": "CAM001",
  "name": "Ngã tư Láng Hạ",
  "stream_url": "rtsp://***:***@192.168.1.100/stream",
  "location": {...},
  "status": "active",
  "roi_config": [],
  "detection_config": {
    "confidence_threshold": 0.5,
    "frame_skip": 2
  },
  "created_at": "2025-10-28T15:30:00Z"
}
```

### Example 2: Update ROI
**Request**:
```
PUT /api/v1/cameras/CAM001/roi
{
  "roi_config": [
    {
      "roi_id": "roi_stopline",
      "name": "Stop Line",
      "type": "line",
      "coordinates": [[0.1, 0.7], [0.9, 0.7]],
      "violation_types": ["red_light"],
      "enabled": true
    },
    {
      "roi_id": "roi_noentry",
      "name": "No Entry Zone",
      "type": "polygon",
      "coordinates": [[0.2,0.3], [0.8,0.3], [0.8,0.6], [0.2,0.6]],
      "violation_types": ["wrong_lane"],
      "enabled": true
    }
  ]
}
```

**Response** (200):
```
{
  "camera_id": "CAM001",
  "roi_config": [...],
  "updated_at": "2025-10-28T16:00:00Z"
}
```

### Example 3: Test Stream
**Request**:
```
POST /api/v1/cameras/CAM001/test-stream
```

**Response**:
```
{
  "status": "success",
  "latency_ms": 145,
  "resolution": "1920x1080",
  "fps": 25,
  "codec": "h264",
  "error": null
}
```

---

## 🔧 Implementation Checklist

### 1. Pydantic Models
- [ ] `CameraCreate` - For POST requests
- [ ] `CameraUpdate` - For PUT requests
- [ ] `CameraResponse` - For responses
- [ ] `ROIConfig` - For ROI objects
- [ ] `DetectionConfig` - For detection settings

### 2. Database Operations
- [ ] CRUD methods trong repository
- [ ] Validation before save
- [ ] Handle duplicates
- [ ] Transaction support (nếu cần)

### 3. Stream Management
- [ ] Test stream connectivity
- [ ] Handle different protocols (RTSP, HTTP)
- [ ] Retry logic
- [ ] Timeout settings

### 4. ROI Validation
- [ ] Coordinate range validation
- [ ] Type validation
- [ ] Polygon closure check
- [ ] Minimum points check

---

## 🧪 Testing Checklist

### API Tests
- [ ] Create camera → Success
- [ ] Create duplicate camera_id → 400 Error
- [ ] Get camera → Return correct data
- [ ] Update ROI → ROI saved correctly
- [ ] Delete camera → Status inactive
- [ ] Test invalid stream → Error message

### Validation Tests
- [ ] Invalid stream_url → 400
- [ ] Invalid ROI coordinates → 400
- [ ] Invalid camera_id format → 400
- [ ] Missing required fields → 422

### Integration Tests
- [ ] Create camera → Appears in list
- [ ] Update camera → Changes reflected
- [ ] Detection uses ROI config
- [ ] Violations reference correct camera

---

## 🔗 Related Prompts

- `api/streams.prompt.md` - Video streaming logic
- `api/violations.prompt.md` - Violations link to cameras
- `database/schema.prompt.md` - Camera schema structure
- `frontend/components.prompt.md` - UI components use API
- `detection/violations.prompt.md` - Detection uses ROI config
