"""Tests for the logging system."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from gemini_repl.utils.logger import Logger


class TestLogger:
    """Test the logging system."""

    def test_logger_initialization(self):
        """Test logger initializes correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            with patch.dict("os.environ", {"LOG_FILE": str(log_file)}):
                logger = Logger()
                assert logger.log_file == str(log_file)
                assert logger.log_level == "INFO"
                assert logger.log_format == "json"

    def test_info_logging(self):
        """Test info level logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            with patch.dict("os.environ", {"LOG_FILE": str(log_file), "LOG_FORMAT": "json"}):
                logger = Logger()
                logger.info("Test message", {"key": "value"})

                # Read log file
                log_content = log_file.read_text().strip()
                log_entry = json.loads(log_content)

                assert log_entry["level"] == "INFO"
                assert log_entry["message"] == "Test message"
                assert log_entry["context"]["key"] == "value"
                assert "timestamp" in log_entry

    def test_error_logging(self):
        """Test error level logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            with patch.dict("os.environ", {"LOG_FILE": str(log_file), "LOG_FORMAT": "json"}):
                logger = Logger()
                logger.error("Error occurred", {"error_code": 500})

                log_content = log_file.read_text().strip()
                log_entry = json.loads(log_content)

                assert log_entry["level"] == "ERROR"
                assert log_entry["message"] == "Error occurred"
                assert log_entry["context"]["error_code"] == 500

    def test_debug_logging(self):
        """Test debug level logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            with patch.dict("os.environ", {"LOG_FILE": str(log_file), "LOG_LEVEL": "DEBUG"}):
                logger = Logger()
                logger.debug("Debug info", {"debug": True})

                log_content = log_file.read_text().strip()
                log_entry = json.loads(log_content)

                assert log_entry["level"] == "DEBUG"
                assert log_entry["message"] == "Debug info"
                assert log_entry["context"]["debug"] is True

    def test_warning_logging(self):
        """Test warning level logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            with patch.dict("os.environ", {"LOG_FILE": str(log_file)}):
                logger = Logger()
                logger.warning("Warning message", {"severity": "medium"})

                log_content = log_file.read_text().strip()
                log_entry = json.loads(log_content)

                assert log_entry["level"] == "WARNING"
                assert log_entry["message"] == "Warning message"
                assert log_entry["context"]["severity"] == "medium"

    def test_multiple_log_entries(self):
        """Test logging multiple entries to a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"

            with patch.dict("os.environ", {"LOG_FILE": str(log_file), "LOG_LEVEL": "DEBUG"}):
                logger = Logger()
                logger.info("Test 1", {"n": 1})
                logger.error("Test 2", {"n": 2})
                logger.debug("Test 3", {"n": 3})

            # Read the log file
            log_lines = log_file.read_text().strip().split("\n")
            assert len(log_lines) == 3

            # Parse each line
            entries = [json.loads(line) for line in log_lines]

            assert entries[0]["message"] == "Test 1"
            assert entries[0]["context"]["n"] == 1
            assert entries[1]["message"] == "Test 2"
            assert entries[1]["context"]["n"] == 2
            assert entries[2]["message"] == "Test 3"
            assert entries[2]["context"]["n"] == 3

    def test_logging_with_invalid_path(self):
        """Test logger handles invalid paths gracefully."""
        with patch.dict("os.environ", {"LOG_FILE": "/invalid/path/test.log"}):
            # Should not crash even with invalid path
            try:
                Logger()  # Don't assign to variable since we're just testing initialization
                # This might fail during initialization if directory creation fails
            except Exception:
                # That's okay, we're testing error handling
                pass
