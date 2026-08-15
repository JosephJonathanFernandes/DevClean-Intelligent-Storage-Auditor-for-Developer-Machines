from dataclasses import dataclass, field
from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.entities.recommendation import Recommendation
from devclean.domain.enums.recommendation_reason import RecommendationReason

@dataclass(frozen=True)
class CleanupDecision:
    """Represents a finalized decision to recommend an item for cleanup, with explanation provenance."""
    item: AuditItem
    recommendation: Recommendation
    priority_score: float
    reason: RecommendationReason
    score_breakdown: dict[str, float] = field(default_factory=dict)
