from typing import Protocol, Iterable
from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.entities.scan_context import ScanContext

class Detector(Protocol):
    """
    Contract for a specific sub-analyzer (e.g., PipCacheDetector).
    Composed into a larger Analyzer.
    """
    
    @property
    def name(self) -> str:
        """The distinct name of the detector (e.g., 'pip_cache')."""
        ...

    def detect(self, context: ScanContext) -> Iterable[AuditItem]:
        """
        Executes the detection logic and yields discovered audit items.
        """
        ...
