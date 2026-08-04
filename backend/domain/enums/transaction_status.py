from enum import Enum

class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    POSTED = "POSTED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
