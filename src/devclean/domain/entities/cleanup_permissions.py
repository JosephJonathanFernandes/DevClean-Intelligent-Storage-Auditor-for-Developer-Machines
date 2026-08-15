from dataclasses import dataclass, field
from typing import Tuple

@dataclass(frozen=True)
class CleanupPermissions:
    """Permissions and system states required for a cleanup action."""
    requires_admin: bool = False
    requires_process_shutdown: Tuple[str, ...] = field(default_factory=tuple)
