from enum import Enum

class AccountType(str, Enum):
    BANK = "BANK"
    CREDIT_CARD = "CREDIT_CARD"
    INVESTMENT = "INVESTMENT"
    LOAN = "LOAN"
    WALLET = "WALLET"
