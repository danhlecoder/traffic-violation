# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Traffic Violation Detection System - A microservices-based real-time traffic monitoring system using YOLO object detection, vehicle tracking, and violation recording. The system processes RTSP/HTTP video streams to detect vehicles, helmets, license plates, and traffic lights, then identifies violations like running red lights and unauthorized ROI entries.

## Architecture

### Microservices Design

The system is decomposed into 4 independent services that communicate via HTTP APIs:

1. **Backend Service** (port 8000) - FastAPI main orchestrator
   - Handles MJPEG streaming with real-time YOLO detection overlay
   - Manages camera configurations and ROI/stopline regions
   - Orchestrates violation detection logic via trackers
   - Coordinates between YOLO and MongoDB services

2. **YOLO Service** (port 8001) - Object detection microservice
   - Two YOLO models: `best1.pt` (vehicles/traffic lights/helmets) and `license_plate.pt` (OCR)
   - Endpoints: `/v1/detect/vehicle` and `/v1/detect/plate`
   - Async processing with ThreadPoolExecutor for CPU-bound operations
   - Returns detections in standardized format: `{bbox, confidence, class_id, class_name}`

3. **MongoDB API Service** (port 8002) - Database abstraction layer
   - CRUD operations for cameras and violations
   - Endpoints under `/v1/cameras` and `/v1/violations`
   - Separates database concerns from main backend logic

4. **Frontend** (port 3000) - React + TypeScript UI
   - Real-time MJPEG stream display
   - Camera management interface
   - Violation history and statistics dashboards

### Critical Architecture Patterns

**Service Communication Flow:**
```
Frontend → Backend (/v1/stream) → YOLO Service (/v1/detect/vehicle)
                                 ↓
                          MongoDB Service (/v1/violations)
```

**Stream Processing Pipeline** (backend/core/streaming/mjpeg.py):
1. VideoCapture reads RTSP frame
2. Frame sent to YOLO Service for detection
3. ObjectTracker assigns persistent track_ids to vehicles (IoU-based ByteTrack)
4. ROIEntryTracker monitors vehicles entering/exiting ROI regions
5. StoplineCrossingDetector checks if tracked vehicles cross stopline
6. Violation records created and saved to MongoDB via API
7. Detections drawn on frame, encoded as JPEG, yielded in MJPEG stream

**State Management:**
- Per-camera trackers maintained in global dicts (`_camera_trackers` in vehicle_tracker.py)
- Tracks persist across frames to maintain vehicle identity
- Violation detection logic uses state machines (NEW → TRACKED → LOST)

## Development Commands

### Starting Services

**Single server deployment (development):**
```bash
bash run.sh up      # Start all services with Docker Compose
bash run.sh down    # Stop all services
```

**Individual services:**
```bash
# MongoDB + Mongo API
docker compose -f docker-compose.mongo.yml up -d --build

# YOLO detection service
docker compose -f docker-compose.yolo.yml up -d --build

# Backend API
docker compose -f docker-compose.backend.yml up -d --build

# Frontend
docker compose -f docker-compose.frontend.yml up -d --build
```

**Manual backend development (without Docker):**
```bash
cd backend
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**Manual YOLO service:**
```bash
cd yolo-service
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

**Frontend development:**
```bash
cd frontend
npm install
npm run dev        # Vite dev server on port 5173
npm run build      # Production build
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose -f docker-compose.backend.yml logs -f
docker compose -f docker-compose.yolo.yml logs -f

# Stream-specific logs (in backend container)
tail -f /app/logs/backend.log
```

### Health Checks

```bash
curl http://localhost:8002/health  # MongoDB API
curl http://localhost:8001/health  # YOLO Service
curl http://localhost:8000/health  # Backend
```

## Configuration Architecture

### Two-Layer Config System

**Static config** (backend/config/server.yaml):
- Server host/port, CORS origins
- Service URLs (yolo_api, mongo_api)
- Database connection parameters
- Logging configuration

**Dynamic config** (backend/.env):
- Detection parameters (YOLO_CONFIDENCE, YOLO_IOU_THRESHOLD)
- Stream settings (STREAM_DEFAULT_FPS, STREAM_DEFAULT_QUALITY)
- Tracking thresholds (TRACKER_IOU_THRESHOLD, TRACKER_MAX_AGE)
- Violation detection parameters (STOPLINE_CROSSING_THRESHOLD, STOPLINE_DETECTION_RANGE)
- Vision parameters for auto-detection (VISION_CANNY_LOW, VISION_HOUGH_THRESHOLD)

**Config loading** (backend/config/config.py):
```python
settings = Settings()  # Singleton
settings.YOLO_CONFIDENCE  # Access parameters
```

### Multi-Server Deployment

For production distributed deployment, see `backend/.env.multi-server`:
- Update YOLO_API_URL, MONGO_API_URL with actual server IPs
- Update `frontend/.env.production.local` with VITE_API_BASE_URL
- See deployment scripts in `deploy-scripts/`

## Key Implementation Details

### YOLO Detection Classes

The system detects **10 object classes**:
- Vehicles: `bus`, `car`, `motorcycle`, `truck`
- Safety: `helmet`, `no_helmet`
- Infrastructure: `license_plate`, `light_red`, `light_yellow`, `light_green`

### Object Tracking Implementation

**ByteTrack-inspired tracker** (backend/core/tracking/vehicle_tracker.py):
- Uses IoU (Intersection over Union) matching between frames
- Assigns persistent `track_id` to each vehicle
- Two-stage matching: high-confidence detections first, then low-confidence
- State machine: New (min_hits threshold) → Tracked → Lost (max_age timeout) → Removed
- Default params: `iou_threshold=0.3`, `max_age=30 frames`, `min_hits=1`

**Critical:** Only vehicles get track_ids. License plates, helmets, and traffic lights are NOT tracked.

### Violation Detection Logic

**Two violation types:**

1. **ROI Entry Violations** (when no stopline configured):
   - Triggered when vehicle first enters configured ROI region
   - Tracked in `backend/core/tracking/roi_entry_tracker.py`
   - State per track_id: outside → inside (triggers violation)
   - Cooldown period: 120 seconds before same vehicle can trigger again

2. **Stopline Crossing Violations** (when stopline configured):
   - Triggered when vehicle bottom bbox (y2) crosses stopline y-coordinate
   - Tracked in `backend/core/tracking/stopline_tracker.py`
   - Detection range: stopline_y ± STOPLINE_DETECTION_RANGE (default 50px)
   - Cooldown: 30 seconds per track_id

**License plate capture:**
- First attempts to find plate in current frame detections (within vehicle bbox)
- If not found, crops vehicle region and runs YOLO detection again on crop
- Plate bbox converted from crop coordinates to frame coordinates

### MJPEG Streaming Architecture

**Real-time optimizations** (backend/core/streaming/mjpeg.py):
```python
# Key parameters
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize lag
DETECTION_SKIP_FRAMES = 0  # Detect every frame (realtime)
skip_frames = 0  # Don't skip reading frames
```

**Error recovery:**
- Consecutive error counter (MAX_CONSECUTIVE_ERRORS=10)
- Auto-reconnect on repeated failures with exponential backoff
- Validates frames before and after detection to prevent corrupted data

**Frame annotation:**
- Location and Vietnam time (UTC+7) overlaid on top-left
- Bounding boxes with class names and track_ids
- ROI polygon drawn (if configured)
- Stopline horizontal line (if configured)

## Database Schema

**Cameras collection:**
```json
{
  "id": "cam001",
  "name": "Camera 1",
  "rtsp": "rtsp://...",
  "location": "Ngã tư ABC",
  "regions": {
    "roi": [{"x": 0.1, "y": 0.3}, ...],  // Normalized coordinates
    "stopLine": {"y": 0.7}  // Normalized or pixel y-coordinate
  }
}
```

**Violations collection:**
```json
{
  "camera_id": "cam001",
  "timestamp": "2025-10-29T10:30:00",
  "vehicle_type": "motorcycle",
  "license_plate": "59A12345",
  "violation_type": "stopline_crossing",
  "image_path": "violations/20251029_103000_track123.jpg",
  "confidence": 0.85
}
```

## API Versioning

All API endpoints use `/v1/` prefix for versioning:
- Backend: `/v1/stream`, `/v1/cameras`, `/v1/detection`, `/v1/violations`
- YOLO Service: `/v1/detect/vehicle`, `/v1/detect/plate`
- MongoDB Service: `/v1/cameras`, `/v1/violations`

When creating new endpoints, always use `/v1/` prefix and follow RESTful conventions.

## Frontend Architecture

**State management:** Zustand stores in `frontend/src/store/`

**Key pages:**
- `/` - Camera list and management
- `/stream/:cameraId` - Real-time MJPEG stream viewer
- `/violations` - Violation history with filters
- `/analytics` - Statistics dashboard

**API client:** Centralized in `frontend/src/services/` with Axios

## Model Requirements

Place YOLO model files in `backend/models/`:
- `best1.pt` - Main detection model (vehicles, helmets, traffic lights, plates)
- `license_plate.pt` - OCR model for license plate character recognition

These models are mounted read-only in Docker containers.

## Common Development Scenarios

### Adding a new detection class

1. Retrain YOLO model with new class
2. Update class list in `yolo-service/main.py` if needed
3. Update frontend display logic in stream component
4. Update violation logic if class should trigger violations

### Modifying tracker parameters

Edit `backend/.env`:
```bash
TRACKER_IOU_THRESHOLD=0.3    # Lower = more lenient matching
TRACKER_MAX_AGE=30           # Frames before track removal
TRACKER_MIN_HITS=1           # Confirmations before track activation
```

### Debugging stream issues

1. Check YOLO service health: `curl http://localhost:8001/health`
2. Verify MongoDB connection in backend logs
3. Monitor frame counter and detection counts in logs (logged every 10 frames)
4. Check for consecutive error messages in stream logs
5. Validate RTSP URL is accessible: `ffplay <rtsp_url>`

### Adding a new violation type

1. Create new tracker in `backend/core/tracking/`
2. Integrate into MJPEG generator in `mjpeg.py`
3. Update violation creation logic in `backend/core/violations/creator.py`
4. Add new violation_type to database schema
5. Update frontend to display new type

## Testing

Currently no automated test suite. Manual testing workflow:

1. Start all services: `bash run.sh up`
2. Add test camera via API or frontend
3. Start stream and verify detections appear
4. Trigger violation (enter ROI or cross stopline)
5. Check MongoDB for violation record
6. Verify violation image saved to filesystem

## Important Notes

- **Language:** Code comments and logs are in Vietnamese, but keep code/variables in English
- **Timezone:** All timestamps use Vietnam time (UTC+7)
- **Performance:** Detection runs on every frame by default (high CPU/GPU usage)
- **State persistence:** Tracker state is in-memory only, resets on service restart
- **RTSP buffering:** System prioritizes real-time over historical accuracy (buffersize=1)
- **Violation cooldowns:** Prevent duplicate violations from same vehicle (30-120s depending on type)
