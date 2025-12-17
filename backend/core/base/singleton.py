"""
Base Singleton Pattern - Helper class cho singleton pattern
Tăng tính kế thừa và tái sử dụng cho các detector/tracker
"""

from typing import Dict, TypeVar, Type

T = TypeVar('T')


class SingletonRegistry:
    """
    Registry quản lý singleton instances
    Hỗ trợ pattern singleton cho các class
    """

    def __init__(self):
        self._instances: Dict[str, object] = {}

    def get_or_create(self, key: str, factory_func) -> object:
        """
        Lấy hoặc tạo instance

        Args:
            key: Key duy nhất cho instance
            factory_func: Hàm tạo instance nếu chưa có

        Returns:
            Instance đã tồn tại hoặc mới tạo
        """
        if key not in self._instances:
            self._instances[key] = factory_func()
        return self._instances[key]

    def reset(self, key: str = None):
        """
        Reset instance hoặc tất cả instances

        Args:
            key: Key của instance cần reset (None = reset tất cả)
        """
        if key:
            if key in self._instances:
                del self._instances[key]
        else:
            self._instances.clear()


def create_singleton_getter(registry: SingletonRegistry, factory_func):
    """
    Tạo hàm getter cho singleton pattern

    Args:
        registry: SingletonRegistry instance
        factory_func: Hàm tạo instance (nhận key làm tham số)

    Returns:
        Hàm getter(key: str) -> instance
    """
    def getter(key: str):
        return registry.get_or_create(key, lambda: factory_func(key))
    return getter






























