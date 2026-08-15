from enum import Enum

class RecommendationReason(Enum):
    LARGE_SAFE_RECLAIM = "large_safe_reclaim"
    DUPLICATE_RUNTIME = "duplicate_runtime"
    STALE_CACHE = "stale_cache"
    UNUSED_ENVIRONMENT = "unused_environment"
    HIGH_DISK_PRESSURE = "high_disk_pressure"
    LOW_RISK_OPTIMIZATION = "low_risk_optimization"
    DEFAULT_RULE = "default_rule"
