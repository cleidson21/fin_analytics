from enum import Enum

class ProviderType(str, Enum):
    PIERRE = "PIERRE"
    MYPROFIT = "MYPROFIT"
    CSV = "CSV"
    YFINANCE = "YFINANCE"
    MANUAL = "MANUAL"
