from typing import Protocol, Iterable
from dataclasses import dataclass

from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.entities.scan_context import ScanContext
from devclean.domain.enums.category import Category

@dataclass(frozen=True)
class AnalyzerMetadata:
    name: str
    category: Category
    priority: int = 100
    requires_admin: bool = False

class Analyzer(Protocol):
    """
    Contract for all storage analyzers (Python, Chrome, Docker, etc.).
    This plugin-oriented architecture allows for easy extension.
    """
    
    @property
    def metadata(self) -> AnalyzerMetadata:
        """Information about this specific analyzer."""
        ...

    def scan(self, context: ScanContext) -> Iterable[AuditItem]:
        """
        Executes the scan and yields discovered audit items.
        Must be implemented as a memory-efficient generator.
        """
        ...
