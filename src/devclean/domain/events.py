from dataclasses import dataclass
from typing import Any
import uuid

from devclean.domain.entities.audit_item import AuditItem

@dataclass(frozen=True)
class Event:
    """Base class for all domain events."""
    scan_id: uuid.UUID
    timestamp: float  # time.perf_counter() for precision

@dataclass(frozen=True)
class AnalyzerStarted(Event):
    analyzer_name: str

@dataclass(frozen=True)
class AnalyzerCompleted(Event):
    analyzer_name: str
    duration_seconds: float
    items_found: int

@dataclass(frozen=True)
class AnalyzerFailed(Event):
    analyzer_name: str
    error: str

@dataclass(frozen=True)
class ItemDiscovered(Event):
    analyzer_name: str
    item: AuditItem
