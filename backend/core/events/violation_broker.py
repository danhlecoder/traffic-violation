"""
Violation Event Broker - Publish/subscribe cho các sự kiện vi phạm
"""

import asyncio
from typing import Dict, Any, Set, Optional

from ...utils.logger import app_logger as logger


class ViolationEventBroker:
    """Broadcast sự kiện vi phạm tới mọi subscriber SSE/WebSocket."""

    def __init__(self) -> None:
        self._subscribers: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self._subscribers.add(queue)
        logger.info("👂 Subscriber mới đăng ký violation events")
        return queue

    async def unsubscribe(self, queue: asyncio.Queue) -> None:
        async with self._lock:
            self._subscribers.discard(queue)
        logger.info("👋 Subscriber violation events rời hàng đợi")

    async def publish(self, event: Dict[str, Any]) -> None:
        async with self._lock:
            subscribers = list(self._subscribers)
        for queue in subscribers:
            await queue.put(event)

    def publish_sync(self, event: Dict[str, Any]) -> None:
        if not self._loop or not self._loop.is_running():
            logger.debug("⚠️ Không có event loop, bỏ qua violation event")
            return
        asyncio.run_coroutine_threadsafe(self.publish(event), self._loop)


_violation_broker = ViolationEventBroker()


def get_violation_event_broker() -> ViolationEventBroker:
    return _violation_broker


def emit_violation_event(event: Dict[str, Any]) -> None:
    try:
        _violation_broker.publish_sync(event)
    except Exception as error:
        logger.error(f"Không thể publish violation event: {error}")
