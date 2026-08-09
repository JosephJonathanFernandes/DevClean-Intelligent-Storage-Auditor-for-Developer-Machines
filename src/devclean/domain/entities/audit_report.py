from dataclasses import dataclass, field
from datetime import datetime
from typing import Sequence

from .audit_item import AuditItem
from .scan_summary import ScanSummary


@dataclass(frozen=True)
class AuditReport:
    """An aggregate root containing all discovered items and their summary."""
    
    items: Sequence[AuditItem]
    summary: ScanSummary
    created_at: datetime = field(default_factory=datetime.utcnow)
