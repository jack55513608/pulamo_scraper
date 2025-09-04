# tests/test_logger_config.py
import unittest
import logging
from logger_config import setup_logger

class TestLoggerConfig(unittest.TestCase):

    def setUp(self):
        """Clean up any existing handlers on the root logger before each test."""
        # Store original handlers
        self.original_handlers = logging.getLogger().handlers[:]
        logging.getLogger().handlers = []

    def tearDown(self):
        """Restore original handlers after each test."""
        logging.getLogger().handlers = self.original_handlers

    def test_setup_logger_configures_correctly(self):
        """Test that setup_logger configures the root logger as expected."""
        # Act
        logger = setup_logger(level=logging.DEBUG)

        # Assert
        root_logger = logging.getLogger()
        
        # 1. Check if the logger returned is the root logger
        self.assertIs(logger, root_logger, "The returned logger should be the root logger.")

        # 2. Check logger level
        self.assertEqual(root_logger.level, logging.DEBUG, "Logger level should be set to DEBUG.")

        # 3. Check handler count and type
        self.assertEqual(len(root_logger.handlers), 1, "There should be exactly one handler.")
        self.assertIsInstance(root_logger.handlers[0], logging.StreamHandler, "The handler should be a StreamHandler.")

        # 4. Check formatter
        formatter = root_logger.handlers[0].formatter
        self.assertIsInstance(formatter, logging.Formatter, "The handler should have a Formatter.")
        # Check the actual format string stored in the formatter
        self.assertEqual(formatter._fmt, '%(levelname)s - %(message)s', "The formatter string is incorrect.")

    def test_setup_logger_clears_existing_handlers(self):
        """Test that setup_logger removes any pre-existing handlers."""
        # Arrange: Add a dummy handler first
        root_logger = logging.getLogger()
        dummy_handler = logging.FileHandler('test.log')
        root_logger.addHandler(dummy_handler)
        self.assertEqual(len(root_logger.handlers), 1, "Dummy handler should be added.")

        # Act
        setup_logger()

        # Assert: The dummy handler should be gone, replaced by the new StreamHandler
        self.assertEqual(len(root_logger.handlers), 1, "Should be only one handler after setup.")
        self.assertIsNot(root_logger.handlers[0], dummy_handler, "The handler should be a new instance, not the dummy one.")
        self.assertIsInstance(root_logger.handlers[0], logging.StreamHandler)

if __name__ == '__main__':
    unittest.main()
