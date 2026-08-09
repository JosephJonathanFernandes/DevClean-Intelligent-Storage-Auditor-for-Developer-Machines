import time
import uuid
from typing import Iterable

from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.entities.scan_context import ScanContext
from devclean.domain.entities.analyzer_result import AnalyzerResult
from devclean.domain.entities.scan_statistics import ScanStatistics
from devclean.domain.events import (
    AnalyzerStarted,
    AnalyzerCompleted,
    AnalyzerFailed,
    ItemDiscovered
)
from devclean.application.events.event_bus import EventBus
from devclean.application.analyzers.registry import AnalyzerRegistry


class AnalyzerPipeline:
    """
    Orchestrates the execution of analyzers, ensuring fault isolation,
    timing, and event emission without coupling to the reporting logic.
    """

    def __init__(self, registry: AnalyzerRegistry, event_bus: EventBus) -> None:
        self._registry = registry
        self._event_bus = event_bus
        self.results: list[AnalyzerResult] = []
        self.statistics: ScanStatistics = ScanStatistics()

    def run(self, context: ScanContext, scan_id: uuid.UUID) -> Iterable[AuditItem]:
        """
        Executes all registered analyzers and yields items as they are found.
        This must be fully consumed to populate self.results and self.statistics.
        """
        self.results = []
        
        analyzers_run = 0
        analyzers_failed = 0
        permission_errors = 0
        
        pipeline_start = time.perf_counter()

        for analyzer in self._registry.get_all():
            if context.cancelled():
                break

            name = analyzer.metadata.name
            analyzers_run += 1
            
            self._event_bus.publish(AnalyzerStarted(
                scan_id=scan_id,
                timestamp=time.perf_counter(),
                analyzer_name=name
            ))

            start_time = time.perf_counter()
            items_found = 0
            total_size = 0
            errors = []

            try:
                # Consume the analyzer's generator
                for item in analyzer.scan(context):
                    if context.cancelled():
                        break
                        
                    items_found += 1
                    total_size += item.size_bytes
                    
                    self._event_bus.publish(ItemDiscovered(
                        scan_id=scan_id,
                        timestamp=time.perf_counter(),
                        analyzer_name=name,
                        item=item
                    ))
                    yield item

                duration = time.perf_counter() - start_time
                self._event_bus.publish(AnalyzerCompleted(
                    scan_id=scan_id,
                    timestamp=time.perf_counter(),
                    analyzer_name=name,
                    duration_seconds=duration,
                    items_found=items_found
                ))
                
            except Exception as e:
                duration = time.perf_counter() - start_time
                analyzers_failed += 1
                error_msg = str(e)
                errors.append(error_msg)
                
                if isinstance(e, PermissionError):
                    permission_errors += 1
                
                self._event_bus.publish(AnalyzerFailed(
                    scan_id=scan_id,
                    timestamp=time.perf_counter(),
                    analyzer_name=name,
                    error=error_msg
                ))

            # Record result regardless of success/failure
            self.results.append(AnalyzerResult(
                analyzer_name=name,
                item_count=items_found,
                total_size_bytes=total_size,
                duration_seconds=duration,
                errors=tuple(errors)
            ))

        pipeline_duration = time.perf_counter() - pipeline_start
        self.statistics = ScanStatistics(
            total_analyzers=len(self._registry.get_all()),
            analyzers_run=analyzers_run,
            analyzers_failed=analyzers_failed,
            scan_duration_seconds=pipeline_duration,
            permission_errors=permission_errors
        )
