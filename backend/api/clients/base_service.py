"""
Base API Service - Class cha cho tất cả API clients
"""

import requests
from typing import Dict, Any, Optional
from abc import ABC
from ...utils.logger import app_logger as logger


class BaseAPIService(ABC):
    """
    Base class cho các API service clients
    Cung cấp các phương thức HTTP chung
    """

    def __init__(self, base_url: str, timeout: int = 10, service_name: str = "API"):
        """
        Args:
            base_url: URL gốc của API service
            timeout: Timeout cho requests (giây)
            service_name: Tên service để logging
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.service_name = service_name

    def health_check(self) -> bool:
        """Kiểm tra sức khỏe service"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """HTTP GET request"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"{self.service_name} - 404 Not Found: {endpoint}")
                return None
            else:
                logger.error(f"{self.service_name} - GET error {response.status_code}: {endpoint}")
                return None

        except requests.Timeout:
            logger.error(f"{self.service_name} - Timeout: {endpoint}")
            return None
        except Exception as e:
            logger.error(f"{self.service_name} - GET error: {e}")
            return None

    def _post(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict]:
        """HTTP POST request"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.post(url, json=data, timeout=self.timeout)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 422:
                # Validation error (422) - có thể do track_id format
                # Log error ngắn gọn, không log response text (có thể chứa base64)
                logger.error(f"{self.service_name} - POST error 422 (Validation Error)")
                # Log metadata violation (không log images để tránh base64 dài)
                safe_data = {
                    'track_id': data.get('track_id'),
                    'vehicle_type': data.get('vehicle_type'),
                    'license_plate': data.get('license_plate'),
                    'timestamp': data.get('timestamp'),
                    'has_images': 'images' in data and data['images'] is not None
                }
                logger.error(f"⚠️ MongoDB API reject data. Metadata: {safe_data}")
                return None
            else:
                logger.error(f"{self.service_name} - POST error {response.status_code}: {response.text}")
                return None

        except requests.Timeout:
            logger.error(f"{self.service_name} - Timeout: {endpoint}")
            return None
        except Exception as e:
            logger.error(f"{self.service_name} - POST error: {e}")
            return None

    def _put(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict]:
        """HTTP PUT request"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.put(url, json=data, timeout=self.timeout)

            if response.status_code == 200:
                try:
                    return response.json()
                except:
                    return {"success": True}
            elif response.status_code == 404:
                logger.warning(f"{self.service_name} - 404 Not Found: {endpoint}")
                return None
            elif response.status_code == 422:
                # Validation error
                error_detail = response.text
                logger.error(f"{self.service_name} - PUT error 422 (Validation): {error_detail}")
                return None
            else:
                logger.error(f"{self.service_name} - PUT error {response.status_code}: {response.text}")
                return None

        except requests.Timeout:
            logger.error(f"{self.service_name} - Timeout: {endpoint}")
            return None
        except Exception as e:
            logger.error(f"{self.service_name} - PUT error: {e}")
            return None

    def _delete(self, endpoint: str) -> bool:
        """HTTP DELETE request"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.delete(url, timeout=self.timeout)

            if response.status_code == 200:
                return True
            elif response.status_code == 404:
                logger.warning(f"{self.service_name} - 404 Not Found: {endpoint}")
                return False
            else:
                logger.error(f"{self.service_name} - DELETE error {response.status_code}")
                return False

        except requests.Timeout:
            logger.error(f"{self.service_name} - Timeout: {endpoint}")
            return False
        except Exception as e:
            logger.error(f"{self.service_name} - DELETE error: {e}")
            return False
