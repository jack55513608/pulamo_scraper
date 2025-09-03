
# notification_manager.py
import time
from typing import Dict

class NotificationManager:
    _instance = None
    _last_notified: Dict[str, float] = {}
    _cooldown_seconds = 1800  # 30 minutes

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NotificationManager, cls).__new__(cls)
        return cls._instance

    def can_notify(self, product_url: str) -> bool:
        """Checks if a notification can be sent for the given product URL."""
        last_notified_time = self._last_notified.get(product_url)
        if last_notified_time:
            elapsed_time = time.time() - last_notified_time
            if elapsed_time < self._cooldown_seconds:
                return False
        return True

    def record_notification(self, product_url: str):
        """Records that a notification has been sent for the given product URL."""
        self._last_notified[product_url] = time.time()

# Singleton instance
notification_manager = NotificationManager()
