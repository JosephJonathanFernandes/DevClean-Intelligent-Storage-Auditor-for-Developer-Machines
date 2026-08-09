from enum import Enum


class RiskLevel(Enum):
    """Represents the risk associated with cleaning up a discovered item."""
    
    SAFE = "safe"           # Can be deleted without side effects (e.g., caches)
    LOW = "low"             # Minor inconvenience if deleted (e.g., browser cache)
    MODERATE = "moderate"   # Might require re-downloading/rebuilding (e.g., node_modules, Docker images)
    HIGH = "high"           # Active environments, user profiles, or containers
