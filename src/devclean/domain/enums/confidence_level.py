from enum import Enum


class ConfidenceLevel(Enum):
    """Represents the confidence of the analyzer's detection."""
    
    VERIFIED = "verified"     # High certainty (e.g., known path, clear signature)
    PROBABLE = "probable"     # Likely correct, but could be false positive
    HEURISTIC = "heuristic"   # Educated guess based on patterns
