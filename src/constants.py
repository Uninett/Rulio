from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOGPATH = BASE_DIR / "logs"
ERROR_LOGPATH = LOGPATH / "errors"
TEST_LOGPATH = LOGPATH / "tests"

TESTING_TENNANT_ID = 42
GLOBAL_TENNANT_ID = 0
