from dataclasses import dataclass
from typing import Tuple, Optional
import uuid


@dataclass(frozen=True)
class CleanupResult:
    """The outcome of an individual cleanup action."""
    action_id: uuid.UUID
    success: bool
    freed_bytes: int
    duration_ms: float
    error: Optional[str] = None
    rollback_available: bool = False


@dataclass(frozen=True)
class ValidationReport:
    """The outcome of the pre-execution validation phase."""
    passed: bool
    warnings: Tuple[str, ...] = ()
    errors: Tuple[str, ...] = ()


@dataclass(frozen=True)
class CleanupExecutionReport:
    """The overall outcome of executing a CleanupPlan."""
    succeeded: int
    failed: int
    skipped: int
    total_freed_bytes: int
    duration_ms: float
    results: Tuple[CleanupResult, ...]
