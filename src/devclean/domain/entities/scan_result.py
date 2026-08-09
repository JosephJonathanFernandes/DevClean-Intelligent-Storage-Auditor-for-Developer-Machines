from dataclasses import dataclass
from typing import Tuple

from .audit_report import AuditReport
from .scan_statistics import ScanStatistics
from .analyzer_result import AnalyzerResult

@dataclass(frozen=True)
class ScanResult:
    """The final result of a complete application scan."""
    report: AuditReport
    statistics: ScanStatistics
    analyzer_results: Tuple[AnalyzerResult, ...]
