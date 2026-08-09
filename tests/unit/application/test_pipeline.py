import pytest
import uuid
from pathlib import Path
from typing import Iterable

from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.entities.scan_context import ScanContext, ScanSettings
from devclean.domain.enums.category import Category
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel
from devclean.domain.enums.platform import Platform
from devclean.domain.services.analyzer import Analyzer, AnalyzerMetadata
from devclean.domain.events import AnalyzerCompleted, AnalyzerFailed

from devclean.application.events.event_bus import EventBus
from devclean.application.analyzers.registry import AnalyzerRegistry
from devclean.application.analyzers.pipeline import AnalyzerPipeline
from devclean.application.use_cases.scan import ScanUseCase


class MockAnalyzer(Analyzer):
    def __init__(self, name: str, items_to_yield: int, should_fail: bool = False):
        self._metadata = AnalyzerMetadata(name=name, category=Category.UNKNOWN)
        self.items_to_yield = items_to_yield
        self.should_fail = should_fail

    @property
    def metadata(self) -> AnalyzerMetadata:
        return self._metadata

    def scan(self, context: ScanContext) -> Iterable[AuditItem]:
        for i in range(self.items_to_yield):
            yield AuditItem(
                path=Path(f"/fake/{self._metadata.name}/{i}"),
                size_bytes=100,
                category=Category.UNKNOWN,
                risk_level=RiskLevel.SAFE,
                description="Fake item",
                confidence=ConfidenceLevel.VERIFIED,
                is_reclaimable=True
            )
        
        if self.should_fail:
            raise PermissionError(f"Access denied for {self._metadata.name}")


def test_pipeline_fault_isolation_and_aggregation():
    # Arrange
    registry = AnalyzerRegistry()
    registry.register(MockAnalyzer("AnalyzerA", 10))
    registry.register(MockAnalyzer("AnalyzerB", 0, should_fail=True))
    registry.register(MockAnalyzer("AnalyzerC", 5))
    registry.freeze()

    event_bus = EventBus()
    
    # We want to track events for verification
    emitted_events = []
    event_bus.subscribe_all(lambda e: emitted_events.append(e))

    pipeline = AnalyzerPipeline(registry, event_bus)
    use_case = ScanUseCase(pipeline)

    context = ScanContext(
        root_paths=(Path("/"),),
        settings=ScanSettings(),
        platform=Platform.LINUX,
        cancelled=lambda: False
    )

    # Act
    report, stats, results = use_case.execute(context)

    # Assert - Items
    assert len(report.items) == 15
    assert report.summary.total_items == 15
    assert report.summary.total_size_bytes == 1500  # 15 * 100

    # Assert - Results
    assert len(results) == 3
    
    res_a = next(r for r in results if r.analyzer_name == "AnalyzerA")
    assert res_a.is_success
    assert res_a.item_count == 10
    
    res_b = next(r for r in results if r.analyzer_name == "AnalyzerB")
    assert not res_b.is_success
    assert "Access denied" in res_b.errors[0]
    
    res_c = next(r for r in results if r.analyzer_name == "AnalyzerC")
    assert res_c.is_success
    assert res_c.item_count == 5

    # Assert - Stats
    assert stats.analyzers_run == 3
    assert stats.analyzers_failed == 1
    assert stats.permission_errors == 1

    # Assert - Events
    failures = [e for e in emitted_events if isinstance(e, AnalyzerFailed)]
    assert len(failures) == 1
    assert failures[0].analyzer_name == "AnalyzerB"
    
    completions = [e for e in emitted_events if isinstance(e, AnalyzerCompleted)]
    assert len(completions) == 2  # A and C completed successfully
