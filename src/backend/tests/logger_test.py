import logging
import pytest


from backend.utils.logger import set_up_logger, set_up_root_logger
from constants import LOGPATH, ERROR_LOGPATH


# Fixtures required for tests
@pytest.fixture
def logger():
    return set_up_logger(__name__)


@pytest.fixture(autouse=True)
def init_root_logger():
    set_up_root_logger()


class TestLogger:
    def test_setup_logger(self):
        logger = set_up_logger(__name__, level=logging.INFO, save_to_file=True, mode="w")
        assert logger.name == __name__
        assert logger.level == 20  # logging.INFO is 20
        assert len(logger.handlers) == 2

    def test_logger(self, logger):
        all_logs_file = LOGPATH / "all_logs.log"
        test_logger_file = LOGPATH / f"{__name__}.log"
        test_error_logger_file = ERROR_LOGPATH / f"{__name__}.log"
        logger.info("This is an info message.")
        logger.error("This is an error message.")
        with open(all_logs_file, "r") as f:
            all_logs_content = f.read()
            assert "This is an info message." in all_logs_content
            assert "This is an error message." in all_logs_content
        with open(test_logger_file, "r") as f:
            test_logger_content = f.read()
            assert "This is an info message." in test_logger_content
            assert "This is an error message." in test_logger_content
        with open(test_error_logger_file, "r") as f:
            test_error_logger_content = f.read()
            assert "This is an error message." in test_error_logger_content
            assert "This is an info message." not in test_error_logger_content
