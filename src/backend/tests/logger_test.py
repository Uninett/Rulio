
import logging
import pytest


from backend.utils.logger import setup_logger, add_file_handler


# Fixtures required for tests
@pytest.fixture
def logger():
    return setup_logger("test_logger")

@pytest.fixture
def file(tmp_path):
    return tmp_path / "test_log.log"


class TestLogger:

    def test_setup_logger(self):
        logger = setup_logger("test_setup_logger")
        assert logger.name == "test_setup_logger"
        assert logger.level == 20  # logging.INFO is 20
        assert len(logger.handlers) == 1

    def test_add_file_handler_info(self, logger, file):
        add_file_handler(logger, file)
        logger.info("This is a test log message.")
        logger.error("This is an error log message.")
        with open(file, 'r') as f:
            logs = f.read()
            assert "This is a test log message." in logs
            assert "This is an error log message." in logs

    def test_add_file_handler_error(self, logger, file):
        add_file_handler(logger, file, level=logging.ERROR)
        logger.info("This is a test log message.")
        logger.error("This is an error log message.")
        with open(file, 'r') as f:
            logs = f.read()
            assert "This is a test log message." not in logs
            assert "This is an error log message." in logs


        