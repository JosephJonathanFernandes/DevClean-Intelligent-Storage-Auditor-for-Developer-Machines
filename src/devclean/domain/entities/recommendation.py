from dataclasses import dataclass, field
from pathlib import Path
from devclean.domain.enums.cleanup import RollbackStrategy, CleanupOperation
from devclean.domain.entities.cleanup_permissions import CleanupPermissions

@dataclass(frozen=True)
class Recommendation:
    """Explains a finding and provides a recommended cleanup action."""
    title: str
    explanation: str
    safety_reason: str
    rollback: RollbackStrategy
    operation: CleanupOperation
    permissions: CleanupPermissions = field(default_factory=CleanupPermissions)
    rollback_notes: str | None = None
    command: str | None = None
    files_affected: tuple[Path, ...] = ()
