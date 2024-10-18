from enum import Enum

class Errors(Enum):
    TICKER_NOT_AVAILABLE = 1
    FAILED_TO_POST_ORDER = 2
    FAILED_TO_HANDLE_ORDER = 3