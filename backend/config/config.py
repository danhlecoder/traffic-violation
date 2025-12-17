"""
Configuration Management - Load settings từ server.yaml và .env
"""

import os
from pathlib import Path
from typing import Any, Union
import yaml
import numpy as np


class Settings:
    """Cài đặt ứng dụng với tối ưu loading và validation"""

    def __init__(self):
        # Tải cấu hình tĩnh từ YAML trước
        self._load_yaml_config()

        # Tải tham số động từ .env
        self._load_env_params()

        # Validate các thiết lập quan trọng
        self._validate_settings()

    @staticmethod
    def _get_env(key: str, default: Any, dtype: type = str) -> Union[str, int, float]:
        """Helper để load và parse biến môi trường với chuyển đổi kiểu"""
        value = os.getenv(key)
        if value is None or value == "":
            return default
        try:
            if dtype == int:
                return int(value)
            elif dtype == float:
                return float(value)
            return str(value)
        except (ValueError, TypeError):
            return default

    def _load_yaml_config(self):
        """Tải cấu hình tĩnh từ server.yaml"""
        config_path = Path(__file__).parent.parent / "config" / "server.yaml"

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        # Cấu hình Server
        server_cfg = config.get("server", {})
        self.HOST: str = server_cfg.get("host", "")
        self.PORT: int = server_cfg.get("port", 0)
        self.ALLOWED_ORIGINS: str = server_cfg.get("allowed_origins", "")

        # Logging
        logging_cfg = config.get("logging", {})
        self.LOG_LEVEL: str = logging_cfg.get("level", "")
        self.LOG_FILE: str = logging_cfg.get("file", "")
        self.LOG_MAX_BYTES: int = logging_cfg.get("max_bytes", 0)
        self.LOG_BACKUP_COUNT: int = logging_cfg.get("backup_count", 0)

        # Dịch vụ bên ngoài
        services_cfg = config.get("services", {})
        self.MONGO_API_URL: str = services_cfg.get("mongo_api", "http://mongo_api:8002")

        # YOLO Vehicle Detection (Local Model)
        yolo_cfg = config.get("yolo_vehicle", {})
        self.YOLO_MODEL_PATH: str = yolo_cfg.get("model_path", "/app/backend/models/best1.pt")
        self.YOLO_DEVICE: str = yolo_cfg.get("device", "cuda")
        self.YOLO_CONF_DEFAULT: float = yolo_cfg.get("conf_threshold", 0.5)
        self.YOLO_IOU_DEFAULT: float = yolo_cfg.get("iou_threshold", 0.45)

        # License Plate OCR (Local Model)
        lp_cfg = config.get("license_plate", {})
        self.LP_MODEL_PATH: str = lp_cfg.get("model_path", "/app/backend/models/license_plate.pt")
        self.LP_DEVICE: str = lp_cfg.get("device", "cuda")
        self.LP_CONF_THRESHOLD: float = lp_cfg.get("conf_threshold", 0.25)  # Giảm để tăng recall
        self.LP_IOU_THRESHOLD: float = lp_cfg.get("iou_threshold", 0.6)

        # Database
        mongo_cfg = config.get("database", {}).get("mongo_camera", {})
        self.MONGO_HOST: str = mongo_cfg.get("host", "")
        self.MONGO_PORT: int = mongo_cfg.get("port", 0)
        self.MONGO_DATABASE: str = mongo_cfg.get("database", "")
        self.MONGO_USERNAME: str = mongo_cfg.get("username", "")
        self.MONGO_PASSWORD: str = mongo_cfg.get("password", "")
        self.MONGO_AUTH_SOURCE: str = mongo_cfg.get("authSource", "")

    def _load_env_params(self):
        """Tải tham số động từ .env với tối ưu parsing"""
        # YOLO Detection
        self.YOLO_CONFIDENCE: float = self._get_env("YOLO_CONFIDENCE", 0.5, float)
        self.YOLO_IOU_THRESHOLD: float = self._get_env("YOLO_IOU_THRESHOLD", 0.45, float)
        self.YOLO_MAX_DETECTIONS: int = self._get_env("YOLO_MAX_DETECTIONS", 100, int)

        # Stream
        # ✅ GIẢM FPS từ 15 → 10 để stream chạy CHẬM HƠN, phát hiện CHÍNH XÁC HƠN
        # FPS thấp hơn = Nhiều thời gian xử lý hơn cho mỗi frame = Detection tốt hơn
        self.STREAM_DEFAULT_FPS: int = self._get_env("STREAM_DEFAULT_FPS", 10, int)
        self.STREAM_DEFAULT_QUALITY: int = self._get_env("STREAM_DEFAULT_QUALITY", 95, int)  # Tăng quality để giảm ghosting/artifacts
        self.STREAM_RECONNECT_TIMEOUT: int = self._get_env("STREAM_RECONNECT_TIMEOUT", 30, int)
        self.STREAM_SKIP_FRAMES: int = self._get_env("STREAM_SKIP_FRAMES", 0, int)
        self.STREAM_DETECTION_WIDTH: int = self._get_env("STREAM_DETECTION_WIDTH", 0, int)

        # MongoDB service caching
        cache_ttl = self._get_env("MONGO_CAMERA_CACHE_TTL", 2.0, float)
        self.MONGO_CAMERA_CACHE_TTL: float = max(0.0, float(cache_ttl))

        # Detection Display
        self.BBOX_THICKNESS: int = self._get_env("BBOX_THICKNESS", 2, int)
        self.FONT_SCALE: float = self._get_env("FONT_SCALE", 0.5, float)
        self.FONT_THICKNESS: int = self._get_env("FONT_THICKNESS", 2, int)

        # Vehicle Density
        self.DENSITY_THRESHOLD_LOW: int = self._get_env("DENSITY_THRESHOLD_LOW", 5, int)
        self.DENSITY_THRESHOLD_MEDIUM: int = self._get_env("DENSITY_THRESHOLD_MEDIUM", 15, int)

        # Stopline Crossing Detection
        self.STOPLINE_DETECTION_RANGE: int = self._get_env("STOPLINE_DETECTION_RANGE", 60, int)
        self.STOPLINE_CROSSING_TIMEOUT: int = self._get_env("STOPLINE_CROSSING_TIMEOUT", 30, int)

        # Async Violation Processing (để tránh lag stream khi lưu DB)
        self.ENABLE_ASYNC_VIOLATION_PROCESSING: bool = self._get_env("ENABLE_ASYNC_VIOLATION_PROCESSING", "true", str).lower() == "true"

        # Vision - Stop Line Detection
        self.VISION_CANNY_LOW: int = self._get_env("VISION_CANNY_LOW", 50, int)
        self.VISION_CANNY_HIGH: int = self._get_env("VISION_CANNY_HIGH", 150, int)
        self.VISION_HOUGH_RHO: int = 1
        self.VISION_HOUGH_THETA: float = np.pi / 180
        self.VISION_HOUGH_THRESHOLD: int = self._get_env("VISION_HOUGH_THRESHOLD", 100, int)
        self.VISION_MIN_LINE_LEN_FACTOR: float = self._get_env("VISION_MIN_LINE_LEN_FACTOR", 0.3, float)
        self.VISION_MAX_GAP_FACTOR: float = self._get_env("VISION_MAX_GAP_FACTOR", 0.05, float)
        self.VISION_MIN_LINE_LEN_MIN_PX: int = self._get_env("VISION_MIN_LINE_LEN_MIN_PX", 100, int)
        self.VISION_MAX_GAP_MIN_PX: int = self._get_env("VISION_MAX_GAP_MIN_PX", 20, int)
        self.VISION_ANGLE_MAX_DEG: float = self._get_env("VISION_ANGLE_MAX_DEG", 10.0, float)
        self.VISION_CENTER_BIAS_RATIO: float = self._get_env("VISION_CENTER_BIAS_RATIO", 0.6, float)
        self.VISION_BOTTOM_MIN_Y_RATIO: float = self._get_env("VISION_BOTTOM_MIN_Y_RATIO", 0.6, float)

        # Tracking đối tượng
        self.TRACKER_IOU_THRESHOLD: float = self._get_env("TRACKER_IOU_THRESHOLD", 0.3, float)
        self.TRACKER_MAX_AGE: int = self._get_env("TRACKER_MAX_AGE", 30, int)
        self.TRACKER_MIN_HITS: int = self._get_env("TRACKER_MIN_HITS", 1, int)
        self.TRACKER_RESET_IDLE_SECONDS: float = self._get_env("TRACKER_RESET_IDLE_SECONDS", 1.0, float)
        self.TRACKER_RESET_ON_IDLE: bool = self._get_env("TRACKER_RESET_ON_IDLE", "true", str).lower() == "true"
        self.TRACKER_CENTER_DISTANCE_PX: float = self._get_env("TRACKER_CENTER_DISTANCE_PX", 120.0, float)
        self.TRACKER_INIT_GRACE_FRAMES: int = self._get_env("TRACKER_INIT_GRACE_FRAMES", 3, int)

        # Trajectory Tracking
        self.TRAJECTORY_ENABLED: bool = self._get_env("TRAJECTORY_ENABLED", "true", str).lower() == "true"
        # ✅ Tăng từ 60 lên 90 để capture xe nhanh tốt hơn (nhiều điểm hơn trong thời gian ngắn)
        self.TRAJECTORY_MAX_POINTS: int = self._get_env("TRAJECTORY_MAX_POINTS", 90, int)
        self.TRAJECTORY_CLEANUP_TIMEOUT: int = self._get_env("TRAJECTORY_CLEANUP_TIMEOUT", 30, int)
        self.TRAJECTORY_LINE_THICKNESS: int = self._get_env("TRAJECTORY_LINE_THICKNESS", 2, int)
        self.TRAJECTORY_POINT_RADIUS: int = self._get_env("TRAJECTORY_POINT_RADIUS", 3, int)
        self.TRAJECTORY_ARROW_LENGTH: int = self._get_env("TRAJECTORY_ARROW_LENGTH", 30, int)
        self.TRAJECTORY_SHOW_SPEED: bool = self._get_env("TRAJECTORY_SHOW_SPEED", "true", str).lower() == "true"
        self.TRAJECTORY_SHOW_TRACK_ID: bool = self._get_env("TRAJECTORY_SHOW_TRACK_ID", "true", str).lower() == "true"
        self.TRAJECTORY_FADE_EFFECT: bool = self._get_env("TRAJECTORY_FADE_EFFECT", "true", str).lower() == "true"
        self.TRAJECTORY_SPEED_IN_KMH: bool = self._get_env("TRAJECTORY_SPEED_IN_KMH", "true", str).lower() == "true"
        self.PIXELS_PER_METER: float = self._get_env("PIXELS_PER_METER", 32.0, float)
        self.TRAJECTORY_PIXELS_BETWEEN_LINES: float = self._get_env("TRAJECTORY_PIXELS_BETWEEN_LINES", 160.0, float)
        # Giữ tên cũ để tương thích ngược
        self.TRAJECTORY_PIXELS_PER_METER: float = self.PIXELS_PER_METER
        # ✅ Giảm từ 5.0 xuống 3.0 giây để trajectory biến mất nhanh hơn (tránh ghost)
        self.TRAJECTORY_ACTIVE_SECONDS: float = self._get_env("TRAJECTORY_ACTIVE_SECONDS", 3.0, float)

    def _validate_settings(self):
        """Validate các thiết lập quan trọng để tránh lỗi runtime"""
        # Kiểm tra phạm vi giá trị
        assert 0 < self.YOLO_CONFIDENCE <= 1, f"YOLO_CONFIDENCE must be in (0, 1], got {self.YOLO_CONFIDENCE}"
        assert 0 < self.YOLO_IOU_THRESHOLD <= 1, f"YOLO_IOU_THRESHOLD must be in (0, 1], got {self.YOLO_IOU_THRESHOLD}"
        assert self.STREAM_DEFAULT_FPS > 0, f"STREAM_DEFAULT_FPS must be > 0, got {self.STREAM_DEFAULT_FPS}"
        assert 10 <= self.STREAM_DEFAULT_QUALITY <= 100, f"STREAM_DEFAULT_QUALITY must be in [10, 100], got {self.STREAM_DEFAULT_QUALITY}"
        assert self.STOPLINE_DETECTION_RANGE > 0, f"STOPLINE_DETECTION_RANGE must be > 0, got {self.STOPLINE_DETECTION_RANGE}"
        assert self.PIXELS_PER_METER > 0, f"PIXELS_PER_METER must be > 0, got {self.PIXELS_PER_METER}"
        assert self.TRAJECTORY_PIXELS_BETWEEN_LINES > 0, f"TRAJECTORY_PIXELS_BETWEEN_LINES must be > 0, got {self.TRAJECTORY_PIXELS_BETWEEN_LINES}"

        # Kiểm tra URLs
        assert self.MONGO_API_URL, "MONGO_API_URL is required"

    @property
    def mongo_uri(self) -> str:
        """Xây dựng MongoDB URI"""
        if not self.MONGO_HOST:
            return ""

        credentials = ""
        if self.MONGO_USERNAME and self.MONGO_PASSWORD:
            credentials = f"{self.MONGO_USERNAME}:{self.MONGO_PASSWORD}@"
            auth_param = f"?authSource={self.MONGO_AUTH_SOURCE}" if self.MONGO_AUTH_SOURCE else ""
        else:
            auth_param = ""

        return f"mongodb://{credentials}{self.MONGO_HOST}:{self.MONGO_PORT}/{self.MONGO_DATABASE}{auth_param}"


settings = Settings()
