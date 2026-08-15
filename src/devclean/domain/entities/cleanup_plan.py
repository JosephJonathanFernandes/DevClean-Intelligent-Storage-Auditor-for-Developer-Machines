from dataclasses import dataclass, field
from datetime import datetime
from typing import Tuple, Dict
import uuid

from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.entities.cleanup_permissions import CleanupPermissions
from devclean.domain.entities.cleanup_decision import CleanupDecision
from devclean.domain.enums.cleanup import RollbackStrategy, CleanupOperation
from devclean.domain.enums.risk_level import RiskLevel





@dataclass(frozen=True)
class CleanupAction:
    """A specific operation to be executed during cleanup."""
    id: uuid.UUID
    decision: CleanupDecision
    requires_confirmation: bool


@dataclass(frozen=True)
class CleanupPlan:
    """A transactional blueprint for a cleanup execution."""
    id: uuid.UUID
    actions: Tuple[CleanupAction, ...]
    estimated_reclaimable_bytes: int
    risk_summary: Dict[RiskLevel, int]
    created_at: datetime = field(default_factory=datetime.utcnow)
