from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.entities.audit_report import AuditReport
from devclean.domain.entities.scan_summary import ScanSummary
from devclean.domain.enums.risk_level import RiskLevel

class AuditReportBuilder:
    """Builds an immutable AuditReport by accumulating items and calculating metrics."""
    
    def __init__(self) -> None:
        self._items: list[AuditItem] = []
        self._total_size_bytes: int = 0
        self._reclaimable_size_bytes: int = 0
        self._safe_count: int = 0
        self._low_count: int = 0
        self._moderate_count: int = 0
        self._high_count: int = 0

    def add_item(self, item: AuditItem) -> None:
        self._items.append(item)
        self._total_size_bytes += item.size_bytes
        
        if item.is_reclaimable:
            self._reclaimable_size_bytes += item.size_bytes
            
        if item.risk_level == RiskLevel.SAFE:
            self._safe_count += 1
        elif item.risk_level == RiskLevel.LOW:
            self._low_count += 1
        elif item.risk_level == RiskLevel.MODERATE:
            self._moderate_count += 1
        elif item.risk_level == RiskLevel.HIGH:
            self._high_count += 1

    def build(self, duration_seconds: float) -> AuditReport:
        """Constructs the immutable AuditReport and ScanSummary."""
        summary = ScanSummary(
            total_items=len(self._items),
            safe_items=self._safe_count,
            low_items=self._low_count,
            moderate_items=self._moderate_count,
            high_items=self._high_count,
            total_size_bytes=self._total_size_bytes,
            reclaimable_size_bytes=self._reclaimable_size_bytes,
            scan_duration_seconds=duration_seconds,
        )
        # Tuple ensures immutability instead of standard list
        return AuditReport(items=tuple(self._items), summary=summary)
