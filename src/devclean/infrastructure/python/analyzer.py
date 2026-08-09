from typing import Iterable

from devclean.domain.services.analyzer import Analyzer, AnalyzerMetadata
from devclean.domain.services.detector import Detector
from devclean.domain.entities.scan_context import ScanContext
from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.enums.category import Category

from .detectors.pip_cache import PipCacheDetector
from .detectors.virtualenvs import VirtualEnvDetector
from .detectors.installations import InstallationDetector
from .detectors.conda import CondaDetector


class PythonAnalyzer(Analyzer):
    """
    Reference implementation of a composite Analyzer.
    It delegates the actual scanning to isolated Detectors.
    """
    
    def __init__(self) -> None:
        self._metadata = AnalyzerMetadata(
            name="python",
            category=Category.UNKNOWN, # Grouping category, individual items specify their own
            priority=10
        )
        self._detectors: list[Detector] = [
            PipCacheDetector(),
            InstallationDetector(),
            VirtualEnvDetector(),
            CondaDetector()
        ]

    @property
    def metadata(self) -> AnalyzerMetadata:
        return self._metadata

    def scan(self, context: ScanContext) -> Iterable[AuditItem]:
        """Runs all registered Python detectors and yields results stream."""
        for detector in self._detectors:
            if context.cancelled():
                break
            
            try:
                items = list(detector.detect(context))
                items.sort(key=lambda i: (i.category.value, str(i.path), -i.size_bytes))
                yield from items
            except Exception as e:
                # For this Phase, we'll let the Pipeline handle it, meaning one failed
                # detector fails the whole PythonAnalyzer. 
                # A more robust approach might be to wrap each detector invocation.
                raise RuntimeError(f"Detector {detector.name} failed: {e}") from e
