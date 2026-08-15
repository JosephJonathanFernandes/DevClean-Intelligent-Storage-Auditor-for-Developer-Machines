from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass(frozen=True)
class RecommendationContext:
    free_disk_bytes: int
    total_disk_bytes: int
    user_policy: str = "balanced"
    recent_history: Dict[str, Any] = field(default_factory=dict)
