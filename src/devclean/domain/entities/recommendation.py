from dataclasses import dataclass
from pathlib import Path
from devclean.domain.enums.rollback_difficulty import RollbackDifficulty

@dataclass(frozen=True)
class Recommendation:
    """Explains a finding and provides a recommended cleanup action."""
    title: str
    explanation: str
    safety_reason: str
    rollback: RollbackDifficulty
    rollback_notes: str | None = None
    command: str | None = None
    files_affected: tuple[Path, ...] = ()
