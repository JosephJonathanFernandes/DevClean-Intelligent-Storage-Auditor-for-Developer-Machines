from typing import Protocol
from pathlib import Path

class PathResolver(Protocol):
    """
    Abstracts platform-specific path resolution to keep detectors platform-independent.
    """
    
    @property
    def local_app_data(self) -> Path: ...
    
    @property
    def roaming_app_data(self) -> Path: ...
    
    @property
    def user_profile(self) -> Path: ...
    
    @property
    def program_files(self) -> Path: ...
    
    @property
    def program_files_x86(self) -> Path | None: ...
    
    @property
    def windows_apps(self) -> Path | None: ...
    
    def expand_env_vars(self, path: str) -> Path:
        """Expands environment variables safely."""
        ...
