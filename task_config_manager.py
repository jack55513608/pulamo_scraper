
# task_config_manager.py
from typing import List, Dict, Any
import config

class TaskConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskConfigManager, cls).__new__(cls)
            cls._instance._load_configs()
        return cls._instance

    def _load_configs(self):
        """Loads configurations from the config module."""
        self._tasks = getattr(config, 'TASKS', [])
        self._blacklisted_sellers = getattr(config, 'BLACKLISTED_SELLERS', [])

    def get_tasks(self) -> List[Dict[str, Any]]:
        """Returns the list of tasks."""
        return self._tasks

    def get_blacklisted_sellers(self) -> List[str]:
        """Returns the list of blacklisted sellers."""
        return self._blacklisted_sellers

# Singleton instance
task_config_manager = TaskConfigManager()
