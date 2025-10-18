"""
Configuration Management - Load settings từ server.yaml và .env
"""

import os
from pathlib import Path
import yaml
import numpy as np


class Settings:
    """Application settings"""

    def __init__(self):
        # Load static config from YAML first
        self._load_yaml_config()
        
        # Load dynamic params from .env
        self._load_env_params()

    def _load_yaml_config(self):
        """Load static config from server.yaml"""
        config_path = Path(__file__).parent.parent / "config" / "server.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        
        # Server
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
        
        # YOLO
        yolo_cfg = config.get("yolo", {})
        self.YOLO_MODEL_PATH: str = yolo_cfg.get("model_path", "")
        self.YOLO_DEVICE: str = yolo_cfg.get("device", "")
        
        # Database
        mongo_cfg = config.get("database", {}).get("mongo_camera", {})
        self.MONGO_HOST: str = mongo_cfg.get("host", "")
        self.MONGO_PORT: int = mongo_cfg.get("port", 0)
        self.MONGO_DATABASE: str = mongo_cfg.get("database", "")
        self.MONGO_USERNAME: str = mongo_cfg.get("username", "")
        self.MONGO_PASSWORD: str = mongo_cfg.get("password", "")
        self.MONGO_AUTH_SOURCE: str = mongo_cfg.get("authSource", "")

    def _load_env_params(self):
        """Load dynamic parameters from .env"""
        # YOLO Detection
        self.YOLO_CONFIDENCE: float = float(os.getenv("YOLO_CONFIDENCE", "0")) if os.getenv("YOLO_CONFIDENCE") else 0.0
        self.YOLO_IOU_THRESHOLD: float = float(os.getenv("YOLO_IOU_THRESHOLD", "0")) if os.getenv("YOLO_IOU_THRESHOLD") else 0.0
        self.YOLO_MAX_DETECTIONS: int = int(os.getenv("YOLO_MAX_DETECTIONS", "0")) if os.getenv("YOLO_MAX_DETECTIONS") else 0
        
        # Stream
        self.STREAM_DEFAULT_FPS: int = int(os.getenv("STREAM_DEFAULT_FPS", "0")) if os.getenv("STREAM_DEFAULT_FPS") else 0
        self.STREAM_DEFAULT_QUALITY: int = int(os.getenv("STREAM_DEFAULT_QUALITY", "0")) if os.getenv("STREAM_DEFAULT_QUALITY") else 0
        self.STREAM_RECONNECT_TIMEOUT: int = int(os.getenv("STREAM_RECONNECT_TIMEOUT", "0")) if os.getenv("STREAM_RECONNECT_TIMEOUT") else 0
        self.STREAM_SKIP_FRAMES: int = int(os.getenv("STREAM_SKIP_FRAMES", "0")) if os.getenv("STREAM_SKIP_FRAMES") else 0
        self.STREAM_DETECTION_WIDTH: int = int(os.getenv("STREAM_DETECTION_WIDTH", "0")) if os.getenv("STREAM_DETECTION_WIDTH") else 0
        
        # Detection Display
        self.BBOX_THICKNESS: int = int(os.getenv("BBOX_THICKNESS", "0")) if os.getenv("BBOX_THICKNESS") else 0
        self.FONT_SCALE: float = float(os.getenv("FONT_SCALE", "0")) if os.getenv("FONT_SCALE") else 0.0
        self.FONT_THICKNESS: int = int(os.getenv("FONT_THICKNESS", "0")) if os.getenv("FONT_THICKNESS") else 0
        
        # Vehicle Density
        self.DENSITY_THRESHOLD_LOW: int = int(os.getenv("DENSITY_THRESHOLD_LOW", "0")) if os.getenv("DENSITY_THRESHOLD_LOW") else 0
        self.DENSITY_THRESHOLD_MEDIUM: int = int(os.getenv("DENSITY_THRESHOLD_MEDIUM", "0")) if os.getenv("DENSITY_THRESHOLD_MEDIUM") else 0
        
        # Vision - Stop Line Detection
        self.VISION_CANNY_LOW: int = int(os.getenv("VISION_CANNY_LOW", "0")) if os.getenv("VISION_CANNY_LOW") else 0
        self.VISION_CANNY_HIGH: int = int(os.getenv("VISION_CANNY_HIGH", "0")) if os.getenv("VISION_CANNY_HIGH") else 0
        self.VISION_HOUGH_RHO: int = 1
        self.VISION_HOUGH_THETA: float = np.pi / 180
        self.VISION_HOUGH_THRESHOLD: int = int(os.getenv("VISION_HOUGH_THRESHOLD", "0")) if os.getenv("VISION_HOUGH_THRESHOLD") else 0
        self.VISION_MIN_LINE_LEN_FACTOR: float = float(os.getenv("VISION_MIN_LINE_LEN_FACTOR", "0")) if os.getenv("VISION_MIN_LINE_LEN_FACTOR") else 0.0
        self.VISION_MAX_GAP_FACTOR: float = float(os.getenv("VISION_MAX_GAP_FACTOR", "0")) if os.getenv("VISION_MAX_GAP_FACTOR") else 0.0
        self.VISION_MIN_LINE_LEN_MIN_PX: int = int(os.getenv("VISION_MIN_LINE_LEN_MIN_PX", "0")) if os.getenv("VISION_MIN_LINE_LEN_MIN_PX") else 0
        self.VISION_MAX_GAP_MIN_PX: int = int(os.getenv("VISION_MAX_GAP_MIN_PX", "0")) if os.getenv("VISION_MAX_GAP_MIN_PX") else 0
        self.VISION_ANGLE_MAX_DEG: float = float(os.getenv("VISION_ANGLE_MAX_DEG", "0")) if os.getenv("VISION_ANGLE_MAX_DEG") else 0.0
        self.VISION_CENTER_BIAS_RATIO: float = float(os.getenv("VISION_CENTER_BIAS_RATIO", "0")) if os.getenv("VISION_CENTER_BIAS_RATIO") else 0.0
        self.VISION_BOTTOM_MIN_Y_RATIO: float = float(os.getenv("VISION_BOTTOM_MIN_Y_RATIO", "0")) if os.getenv("VISION_BOTTOM_MIN_Y_RATIO") else 0.0

        # Vision - ROI (road area) detection via color seed + Mahalanobis + shape refine
        # Các tham số sau phục vụ Cell B trong notebook (seed màu đáy + Mahalanobis)
        self.ROI_PROC_WIDTH: int = int(os.getenv("ROI_PROC_WIDTH", "0")) if os.getenv("ROI_PROC_WIDTH") else 0
        self.ROI_BOTTOM_START_RATIO: float = float(os.getenv("ROI_BOTTOM_START_RATIO", "0")) if os.getenv("ROI_BOTTOM_START_RATIO") else 0.0
        self.ROI_MD2_THRESH: float = float(os.getenv("ROI_MD2_THRESH", "0")) if os.getenv("ROI_MD2_THRESH") else 0.0  # <0 -> auto
        self.ROI_MD2_AUTO_PERCENTILE: float = float(os.getenv("ROI_MD2_AUTO_PERCENTILE", "0")) if os.getenv("ROI_MD2_AUTO_PERCENTILE") else 0.0
        self.ROI_MIN_AREA_RATIO: float = float(os.getenv("ROI_MIN_AREA_RATIO", "0")) if os.getenv("ROI_MIN_AREA_RATIO") else 0.0
        self.ROI_MORPH_CLOSE_K: int = int(os.getenv("ROI_MORPH_CLOSE_K", "0")) if os.getenv("ROI_MORPH_CLOSE_K") else 0
        self.ROI_MORPH_OPEN_K: int = int(os.getenv("ROI_MORPH_OPEN_K", "0")) if os.getenv("ROI_MORPH_OPEN_K") else 0
        self.ROI_ERODE_K: int = int(os.getenv("ROI_ERODE_K", "0")) if os.getenv("ROI_ERODE_K") else 0
        self.ROI_YCUT_RATIO: float = float(os.getenv("ROI_YCUT_RATIO", "0")) if os.getenv("ROI_YCUT_RATIO") else 0.0
        self.ROI_BIN_COUNT: int = int(os.getenv("ROI_BIN_COUNT", "0")) if os.getenv("ROI_BIN_COUNT") else 0
        self.ROI_SIDE_LEFT_PCTL: float = float(os.getenv("ROI_SIDE_LEFT_PCTL", "0")) if os.getenv("ROI_SIDE_LEFT_PCTL") else 0.0
        self.ROI_SIDE_RIGHT_PCTL: float = float(os.getenv("ROI_SIDE_RIGHT_PCTL", "0")) if os.getenv("ROI_SIDE_RIGHT_PCTL") else 0.0
        self.ROI_TOP_MIN_RATIO: float = float(os.getenv("ROI_TOP_MIN_RATIO", "0")) if os.getenv("ROI_TOP_MIN_RATIO") else 0.0
        self.ROI_TOP_MAX_RATIO: float = float(os.getenv("ROI_TOP_MAX_RATIO", "0")) if os.getenv("ROI_TOP_MAX_RATIO") else 0.0
        self.ROI_TOP_FROM_MASK_PCTL: float = float(os.getenv("ROI_TOP_FROM_MASK_PCTL", "0")) if os.getenv("ROI_TOP_FROM_MASK_PCTL") else 0.0

    @property
    def mongo_uri(self) -> str:
        """Build MongoDB URI"""
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
