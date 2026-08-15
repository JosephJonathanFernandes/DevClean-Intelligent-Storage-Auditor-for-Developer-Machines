from dataclasses import dataclass
from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.entities.recommendation import Recommendation
from devclean.domain.enums.recommendation_reason import RecommendationReason

@dataclass(frozen=True)
class CleanupRecommendation:
    """Represents a decision to recommend an item for cleanup, with priority scoring."""
    item: AuditItem
    recommendation: Recommendation
    priority_score: float
    reason: RecommendationReason
