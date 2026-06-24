from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOGPATH = BASE_DIR / "logs"
ERROR_LOGPATH = LOGPATH / "errors"
TEST_LOGPATH = LOGPATH / "tests"

GLOBAL_TENANT_ID = 1

DIRECTION_CHOICES = ["source", "destination", "reverse_source", "reverse_destination"]
DIRECTION_CHOICES_DJANGO = [(direction, direction) for direction in DIRECTION_CHOICES]
