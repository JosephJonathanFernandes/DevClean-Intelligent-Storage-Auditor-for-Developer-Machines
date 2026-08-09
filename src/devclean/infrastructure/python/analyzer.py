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
                # We yield from the detector directly.
                # If a specific detector crashes, we let it bubble up to the pipeline
                # orchestrator which handles fault isolation per Analyzer. 
                # (Ideally, we might want isolation per-detector, but for this reference 
                # architecture we rely on the Pipeline's isolation at the Analyzer level,
                # or we could catch it here if we wanted fine-grained isolation.)
                yield from detector.detect(context)
            except Exception as e:
                # For this Phase, we'll let the Pipeline handle it, meaning one failed
                # detector fails the whole PythonAnalyzer. 
                # A more robust approach might be to wrap each detector invocation.
                raise RuntimeError(f"Detector {detector.name} failed: {e}") from e
