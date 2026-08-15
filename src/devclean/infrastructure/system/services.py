import os
from pathlib import Path
from datetime import datetime
from typing import Mapping

from devclean.domain.services.platform_services import (
    PlatformServices, PathResolver, FilesystemService, ClockService, EnvironmentService
)

class DefaultPathResolver(PathResolver):
    @property
    def local_app_data(self) -> Path:
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        
    @property
    def roaming_app_data(self) -> Path:
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        
    @property
    def user_profile(self) -> Path:
        return Path.home()
        
    @property
    def program_files(self) -> Path:
        return Path(os.environ.get("ProgramW6432", "C:\\Program Files"))
        
    @property
    def program_files_x86(self) -> Path | None:
        return Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"))
        
    @property
    def windows_apps(self) -> Path | None:
        return self.local_app_data / "Microsoft" / "WindowsApps"
        
    def expand_env_vars(self, path: str) -> Path:
        return Path(os.path.expandvars(path))

class DefaultFilesystemService(FilesystemService):
    def exists(self, path: Path) -> bool:
        return path.exists()
        
    def is_file(self, path: Path) -> bool:
        return path.is_file()
        
    def is_dir(self, path: Path) -> bool:
        return path.is_dir()
        
    def size(self, path: Path) -> int:
        return path.stat().st_size
        
    def modified_time(self, path: Path) -> datetime:
        return datetime.fromtimestamp(path.stat().st_mtime)
        
    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

class DefaultClockService(ClockService):
    def now(self) -> datetime:
        return datetime.now()

class DefaultEnvironmentService(EnvironmentService):
    def get(self, key: str, default: str | None = None) -> str | None:
        return os.environ.get(key, default)
        
    def get_all(self) -> Mapping[str, str]:
        return dict(os.environ)

class DefaultPlatformServices(PlatformServices):
    def __init__(self):
        self._paths = DefaultPathResolver()
        self._fs = DefaultFilesystemService()
        self._clock = DefaultClockService()
        self._env = DefaultEnvironmentService()
        
    @property
    def paths(self) -> PathResolver:
        return self._paths
        
    @property
    def fs(self) -> FilesystemService:
        return self._fs
        
    @property
    def clock(self) -> ClockService:
        return self._clock
        
    @property
    def env(self) -> EnvironmentService:
        return self._env
