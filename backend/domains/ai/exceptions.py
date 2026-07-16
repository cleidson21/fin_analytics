class AIBaseException(Exception):
    pass

class AITimeoutException(AIBaseException):
    pass

class AIRateLimitException(AIBaseException):
    pass

class AIApiUnavailableException(AIBaseException):
    pass

class AIInvalidKeyException(AIBaseException):
    pass

class AIQuotaExceededException(AIBaseException):
    pass
