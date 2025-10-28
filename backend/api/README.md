# API Structure

## Cấu trúc thư mục

```
api/
├── __init__.py          # Export routers từ v1
├── lifecycle.py         # Lifecycle events (startup/shutdown)
├── middleware.py        # CORS và middleware khác
└── v1/                  # API Version 1
    ├── __init__.py      # Export các routers v1
    ├── cameras.py       # Camera CRUD endpoints
    ├── detection.py     # Detection endpoints (stopline detection)
    ├── streams.py       # Video streaming endpoints
    └── violations.py    # Violation CRUD endpoints
```

## API Versioning

Tất cả endpoints API được tổ chức theo version trong thư mục `v1/`:

- **v1/** - API Version 1 (hiện tại)
  - `/v1/cameras` - Quản lý cameras
  - `/v1/stream` - Video streaming
  - `/v1/detection` - Detection services
  - `/v1/violations` - Quản lý vi phạm

## Thêm API Version mới

Để thêm version mới (v2):

1. Tạo thư mục `api/v2/`
2. Copy hoặc tạo mới các router files
3. Update `api/__init__.py` để export v2 routers
4. Update `app.py` để include v2 routers với prefix `/v2`

## Shared Components

- `lifecycle.py` - Startup/shutdown events (shared across versions)
- `middleware.py` - CORS và middleware (shared across versions)
