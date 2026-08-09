from typing import Iterable

from devclean.domain.services.analyzer import Analyzer, AnalyzerMetadata
from devclean.domain.services.detector import Detector
from devclean.domain.entities.scan_context import ScanContext
from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.enums.category import Category

from .detectors.ai_models import ChromeAIModelDetector
from .detectors.profiles import ChromeProfileDetector
from .detectors.cache import ChromeCacheDetector


class ChromeAnalyzer(Analyzer):
    """
    Reference implementation of a composite Analyzer for Chrome artifacts.
    """
    
    def __init__(self) -> None:
        self._metadata = AnalyzerMetadata(
            name="chrome",
            category=Category.UNKNOWN,
            priority=20
        )
        self._detectors: list[Detector] = [
            ChromeAIModelDetector(),
            ChromeProfileDetector(),
            ChromeCacheDetector()
        ]

    @property
    def metadata(self) -> AnalyzerMetadata:
        return self._metadata

    def scan(self, context: ScanContext) -> Iterable[AuditItem]:
        for detector in self._detectors:
            if context.cancelled():
                break
            
            try:
                yield from detector.detect(context)
            except Exception as e:
                raise RuntimeError(f"Detector {detector.name} failed: {e}") from e
