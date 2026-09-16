from enum import Enum

class GoalStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ACHIEVED = "ACHIEVED"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"
