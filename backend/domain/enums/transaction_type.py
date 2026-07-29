from enum import Enum

class TransactionType(str, Enum):
    PURCHASE = "PURCHASE"
    TRANSFER = "TRANSFER"
    PAYMENT = "PAYMENT"
    PIX = "PIX"
    TED = "TED"
    DOC = "DOC"
    REFUND = "REFUND"
    WITHDRAWAL = "WITHDRAWAL"
    FEE = "FEE"
    INTEREST = "INTEREST"
    OTHER = "OTHER"
