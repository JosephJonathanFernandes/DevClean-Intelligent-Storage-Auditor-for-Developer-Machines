from dataclasses import dataclass, field
from typing import Sequence

@dataclass(frozen=True)
class ScanStatistics:
    """Operational metrics for the entire scan process."""
    
    analyzers_run: int = 0
    analyzers_failed: int = 0
    directories_scanned: int = 0
    scan_duration_seconds: float = 0.0
    permission_errors: int = 0
    skipped_paths: int = 0
