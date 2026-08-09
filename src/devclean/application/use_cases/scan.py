import uuid
from typing import Tuple

from devclean.domain.entities.scan_context import ScanContext
from devclean.domain.entities.audit_report import AuditReport
from devclean.domain.entities.scan_statistics import ScanStatistics
from devclean.domain.entities.scan_result import ScanResult
from devclean.domain.entities.analyzer_result import AnalyzerResult
from devclean.application.analyzers.pipeline import AnalyzerPipeline
from devclean.application.reporting.builder import AuditReportBuilder


class ScanUseCase:
    """
    Application entry point for running a scan.
    Coordinates the pipeline and the report builder.
    """
    
    def __init__(self, pipeline: AnalyzerPipeline) -> None:
        self._pipeline = pipeline

    def execute(self, context: ScanContext) -> ScanResult:
        """
        Executes the scan, aggregates the results, and returns the final report and stats.
        """
        scan_id = uuid.uuid4()
        builder = AuditReportBuilder()
        
        # 1. Run pipeline (returns a generator)
        item_stream = self._pipeline.run(context, scan_id)
        
        # 2. Consume the stream into the builder
        for item in item_stream:
            builder.add_item(item)
            
        # 3. Build the final report
        # The pipeline's statistics are now fully populated
        stats = self._pipeline.statistics
        report = builder.build(duration_seconds=stats.scan_duration_seconds)
        
        return ScanResult(
            report=report,
            statistics=stats,
            analyzer_results=tuple(self._pipeline.results)
        )
