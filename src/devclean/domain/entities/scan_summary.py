from dataclasses import dataclass, field
from .audit_item import AuditItem


@dataclass(frozen=True)
class ScanSummary:
    """A summary of the scan results."""
    
    total_items: int
    safe_items: int
    low_items: int
    moderate_items: int
    high_items: int
    
    total_size_bytes: int
    reclaimable_size_bytes: int
    
    scan_duration_seconds: float
