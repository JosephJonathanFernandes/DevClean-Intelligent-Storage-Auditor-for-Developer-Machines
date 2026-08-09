from dataclasses import dataclass, field
from datetime import datetime
from typing import Sequence
import uuid

from .audit_item import AuditItem
from .scan_summary import ScanSummary


@dataclass(frozen=True)
class AuditReport:
    """An aggregate root containing all discovered items and their summary."""
    
    items: Sequence[AuditItem]
    summary: ScanSummary
    created_at: datetime = field(default_factory=datetime.utcnow)
    id: uuid.UUID = field(default_factory=uuid.uuid4)
