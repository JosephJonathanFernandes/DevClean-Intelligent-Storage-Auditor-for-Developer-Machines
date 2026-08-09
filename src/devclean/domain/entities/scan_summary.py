from dataclasses import dataclass, field
from .audit_item import AuditItem


@dataclass(frozen=True)
class ScanSummary:
    """A summary of the scan results."""
    
    total_items: int = 0
    safe_items: int = 0
    low_items: int = 0
    moderate_items: int = 0
    high_items: int = 0
    
    total_size_bytes: int = 0
    reclaimable_size_bytes: int = 0
    
    scan_duration_seconds: float = 0.0
