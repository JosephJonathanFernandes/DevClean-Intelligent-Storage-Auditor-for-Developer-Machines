from typing import Iterable
from devclean.domain.entities.scan_context import ScanContext
from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.enums.category import Category
from devclean.domain.services.analyzer import Analyzer, AnalyzerMetadata
from devclean.domain.services.detector import Detector
from .detectors import WSLDistroDetector

class WSLAnalyzer(Analyzer):
    def __init__(self):
        self._metadata = AnalyzerMetadata(
            name="wsl",
            category=Category.SYSTEM_CACHE,
            priority=25
        )
        self._detectors: list[Detector] = [
            WSLDistroDetector()
        ]

    @property
    def metadata(self) -> AnalyzerMetadata:
        return self._metadata

    def scan(self, context: ScanContext) -> Iterable[AuditItem]:
        for detector in self._detectors:
            if context.cancelled():
                break
            
            try:
                items = list(detector.detect(context))
                items.sort(key=lambda i: (i.category.value, str(i.path), -i.size_bytes))
                yield from items
            except Exception as e:
                raise RuntimeError(f"Detector {detector.name} failed: {e}") from e
