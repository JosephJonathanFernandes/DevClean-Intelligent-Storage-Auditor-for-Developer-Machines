from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from devclean.domain.enums.platform import Platform
from devclean.domain.services.path_resolver import PathResolver

@dataclass(frozen=True)
class ScanSettings:
    """Configuration for the scan operation."""
    exclude_patterns: tuple[str, ...] = ()
    include_hidden: bool = False
    follow_symlinks: bool = False

@dataclass(frozen=True)
class ScanContext:
    """Explicit context provided to analyzers to avoid global state dependencies."""
    root_paths: tuple[Path, ...]
    settings: ScanSettings
    platform: Platform
    paths: PathResolver
    
    # Cancellation token: analyzers should check this periodically and return if True.
    cancelled: Callable[[], bool]
