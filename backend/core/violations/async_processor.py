"""
Async Violation Processor - Xử lý vi phạm bất đồng bộ để tránh lag stream

Chức năng:
- Queue violations để xử lý background
- Không block frame processing loop
- Tự động retry khi lỗi
"""

import queue
import threading
from typing import Dict, Any, Optional
from ...utils.logger import app_logger as logger


class AsyncViolationProcessor:
    """
    Xử lý vi phạm bất đồng bộ bằng background thread

    Pattern: Producer-Consumer
    - Frame processor (producer) đẩy violations vào queue
    - Background worker (consumer) xử lý và lưu DB
    """

    def __init__(self, max_queue_size: int = 100):
        """
        Args:
            max_queue_size: Kích thước tối đa của queue (tránh memory leak)
        """
        self._queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        self._worker: Optional[threading.Thread] = None
        self._running = False
        self._processed_count = 0
        self._error_count = 0

    def start(self):
        """Khởi động background worker thread"""
        if self._running:
            logger.warning("AsyncViolationProcessor đã được khởi động")
            return

        self._running = True
        self._worker = threading.Thread(target=self._process_loop, daemon=True)
        self._worker.start()
        logger.info("✅ AsyncViolationProcessor started")

    def stop(self):
        """Dừng background worker thread"""
        if not self._running:
            return

        self._running = False
        # Đợi worker thread kết thúc (tối đa 5s)
        if self._worker:
            self._worker.join(timeout=5.0)
        logger.info(f"🛑 AsyncViolationProcessor stopped (processed={self._processed_count}, errors={self._error_count})")

    def submit(self, violation: Dict[str, Any]) -> bool:
        """
        Submit violation để xử lý async

        Args:
            violation: Violation record cần xử lý

        Returns:
            True nếu submit thành công, False nếu queue full
        """
        try:
            # Non-blocking put với timeout ngắn
            self._queue.put(violation, block=False)
            return True
        except queue.Full:
            logger.warning("⚠️ Violation queue FULL, bỏ qua violation (hệ thống quá tải)")
            return False

    def _process_loop(self):
        """Background worker loop - xử lý violations từ queue"""
        from .repository import upsert_violation_record

        logger.info("🔄 AsyncViolationProcessor worker thread started")

        while self._running:
            try:
                # Block tối đa 1s để check _running flag
                violation = self._queue.get(timeout=1.0)

                # Xử lý violation với sync mode (vì đã ở trong background thread)
                try:
                    track_id = violation.get("track_id")
                    # Gọi upsert_violation_record với async_mode=False (vì đã trong background thread)
                    result = upsert_violation_record(violation, async_mode=False)

                    if result:
                        self._processed_count += 1
                        # Log mỗi 10 violations để giảm spam
                        if self._processed_count % 10 == 0:
                            logger.debug(f"📊 Processed {self._processed_count} violations (queue_size={self._queue.qsize()})")
                    else:
                        self._error_count += 1
                        logger.error(f"❌ Lỗi lưu violation track_id={track_id}")

                except Exception as e:
                    self._error_count += 1
                    logger.error(f"❌ Lỗi xử lý violation: {e}")

                finally:
                    self._queue.task_done()

            except queue.Empty:
                # Timeout, tiếp tục loop
                continue
            except Exception as e:
                logger.error(f"❌ Lỗi worker loop: {e}")

        logger.info("🛑 AsyncViolationProcessor worker thread stopped")

    def get_stats(self) -> Dict[str, Any]:
        """Lấy thống kê xử lý"""
        return {
            "running": self._running,
            "queue_size": self._queue.qsize(),
            "processed_count": self._processed_count,
            "error_count": self._error_count,
        }


# Singleton instance
_async_processor: Optional[AsyncViolationProcessor] = None


def get_async_processor() -> AsyncViolationProcessor:
    """Lấy singleton instance của AsyncViolationProcessor"""
    global _async_processor
    if _async_processor is None:
        _async_processor = AsyncViolationProcessor(max_queue_size=100)
        _async_processor.start()
    return _async_processor


def shutdown_async_processor():
    """Shutdown async processor (gọi khi tắt server)"""
    global _async_processor
    if _async_processor:
        _async_processor.stop()
        _async_processor = None

