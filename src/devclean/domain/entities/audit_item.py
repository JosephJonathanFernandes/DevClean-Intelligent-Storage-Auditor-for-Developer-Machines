from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import uuid

from devclean.domain.enums.category import Category
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel
from devclean.domain.entities.recommendation import Recommendation


@dataclass(frozen=True)
class AuditItem:
    """Represents a discovered storage artifact on the system."""
    
    path: Path
    size_bytes: int
    category: Category
    risk_level: RiskLevel
    description: str
    confidence: ConfidenceLevel
    recommendation: Recommendation | None = None
    
    last_modified: datetime | None = None
    owner: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    is_reclaimable: bool = True
    id: uuid.UUID = field(default_factory=uuid.uuid4)
