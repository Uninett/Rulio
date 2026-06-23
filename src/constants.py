from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOGPATH = BASE_DIR / "logs"
ERROR_LOGPATH = LOGPATH / "errors"
TEST_LOGPATH = LOGPATH / "tests"

TESTING_TENANT_ID = 42
GLOBAL_TENANT_ID = 1

DIRECTION_OPTIONS = ["source", "destination", "reverse_source", "reverse_destination"]
