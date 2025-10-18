# Backend Structure

## Directory Layout

```
backend/
├── api/                     # FastAPI routers (REST endpoints)
├── core/                    # Application core (config, startup, middleware)
├── models/                  # ML model files
├── schemas/                 # Pydantic data models
├── services/                # Business logic & service layer
├── utils/                   # Utilities (logging, helpers)
└── config/                  # Configuration files (YAML)
```

## Module Responsibilities

### `api/` - API Endpoints
- `cameras.py` - Camera CRUD operations
- `detection.py` - Stopline detection from image
- `density.py` - Vehicle density info
- `streams.py` - MJPEG streaming

### `core/` - Application Core
- `config.py` - Settings loader (YAML + .env)
- `constants.py` - Constants (colors, thresholds)
- `middleware.py` - CORS configuration
- `startup.py` - Lifespan events (startup/shutdown)

### `services/` - Business Logic
- `database.py` - MongoDB connection (singleton)
- `yolo_detector.py` - YOLO model inference
- `stopline_detector.py` - Stopline detection (Canny + Hough)
- `detection_filters.py` - Filter detections by ROI
- `image_processing.py` - Image utilities (crop, normalize)
- `streaming.py` - RTSP streaming service
- `vehicle_density.py` - Vehicle counting & classification

### `schemas/` - Data Models
- `camera.py` - Camera, CameraRegion, Point schemas

### `utils/` - Utilities
- `logger.py` - Logging configuration

## Key Design Patterns

1. **Singleton Pattern**: YOLO detector, MongoDB client
2. **Service Layer**: Business logic tách biệt khỏi API
3. **Dependency Injection**: Settings, loggers inject qua imports
4. **Separation of Concerns**: Mỗi module có trách nhiệm rõ ràng

## Import Convention

```python
# Core
from ..core.config import settings
from ..core.constants import COLORS_BY_CLASS

# Services
from ..services.yolo_detector import get_yolo_detector
from ..services.detection_filters import filter_detections_by_roi

# Schemas
from ..schemas.camera import Camera, CameraRegion

# Utils
from ..utils.logger import app_logger
```

## Recent Refactoring (2025-10-18)

- Tách `detection.py` từ `streams.py`
- Tách `detection_filters.py` từ `yolo_detector.py`
- Tách `image_processing.py` từ `stopline_detector.py`
- Đổi tên: `detector.py` → `yolo_detector.py`
- Đổi tên: `detect_line.py` → `stopline_detector.py`
- Đổi tên thư mục: `model/` → `models/`
