from enum import Enum

class RollbackDifficulty(Enum):
    """Represents the difficulty of undoing a cleanup action."""
    AUTOMATIC = "automatic"
    EASY = "easy"
    MANUAL = "manual"
    DIFFICULT = "difficult"
    IMPOSSIBLE = "impossible"
