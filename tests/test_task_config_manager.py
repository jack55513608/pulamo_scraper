# tests/test_task_config_manager.py
import unittest
from unittest.mock import patch
from task_config_manager import TaskConfigManager

class TestTaskConfigManager(unittest.TestCase):

    def setUp(self):
        """Reset the singleton before each test to ensure test isolation."""
        TaskConfigManager._instance = None
        self.manager = TaskConfigManager()

    def tearDown(self):
        """Clean up the singleton after tests."""
        TaskConfigManager._instance = None

    @patch('task_config_manager.config')
    def test_load_configs_successfully(self, mock_config):
        """
        Test that the manager correctly loads tasks and blacklisted sellers
        from a mocked config module.
        """
        # Arrange
        mock_config.TASKS = [{'name': 'task1'}]
        mock_config.BLACKLISTED_SELLERS = ['seller1']

        # Act
        self.manager.load_configs()

        # Assert
        self.assertEqual(self.manager.get_tasks(), [{'name': 'task1'}])
        self.assertEqual(self.manager.get_blacklisted_sellers(), ['seller1'])

    @patch('task_config_manager.config')
    def test_load_configs_when_missing(self, mock_config):
        """
        Test that the manager handles cases where TASKS or BLACKLISTED_SELLERS
        are missing, defaulting to empty lists.
        """
        # Arrange
        # Simulate a config module where these attributes do not exist.
        # The hasattr check in getattr will handle this.
        if hasattr(mock_config, 'TASKS'):
            delattr(mock_config, 'TASKS')
        if hasattr(mock_config, 'BLACKLISTED_SELLERS'):
            delattr(mock_config, 'BLACKLISTED_SELLERS')

        # Act
        self.manager.load_configs()

        # Assert
        self.assertEqual(self.manager.get_tasks(), [])
        self.assertEqual(self.manager.get_blacklisted_sellers(), [])

    @patch('task_config_manager.config')
    def test_load_configs_when_partially_missing(self, mock_config):
        """
        Test that the manager handles when only one of the configs is missing.
        """
        # Arrange
        mock_config.TASKS = [{'name': 'task1'}]
        if hasattr(mock_config, 'BLACKLISTED_SELLERS'):
            delattr(mock_config, 'BLACKLISTED_SELLERS')

        # Act
        self.manager.load_configs()

        # Assert
        self.assertEqual(len(self.manager.get_tasks()), 1)
        self.assertEqual(self.manager.get_blacklisted_sellers(), [])

if __name__ == '__main__':
    unittest.main()
