import pytest
from pathlib import Path

from devclean.domain.entities.scan_context import ScanContext, ScanSettings
from devclean.domain.enums.platform import Platform
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel
from devclean.domain.enums.rollback_difficulty import RollbackDifficulty
from datetime import datetime
from typing import Mapping

from devclean.domain.services.platform_services import PlatformServices, PathResolver, FilesystemService, ClockService, EnvironmentService
from devclean.infrastructure.python.detectors.pip_cache import PipCacheDetector
from devclean.infrastructure.python.detectors.virtualenvs import VirtualEnvDetector
from devclean.infrastructure.python.detectors.installations import InstallationDetector

class MockPathResolver(PathResolver):
    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path
        self._local_app_data = tmp_path / "AppData" / "Local"
        self._user_profile = tmp_path / "Users" / "TestUser"
        self._program_files = tmp_path / "Program Files"
        
        self._local_app_data.mkdir(parents=True, exist_ok=True)
        self._user_profile.mkdir(parents=True, exist_ok=True)
        self._program_files.mkdir(parents=True, exist_ok=True)

    @property
    def local_app_data(self) -> Path: return self._local_app_data
    @property
    def roaming_app_data(self) -> Path: return self.tmp_path / "AppData" / "Roaming"
    @property
    def user_profile(self) -> Path: return self._user_profile
    @property
    def program_files(self) -> Path: return self._program_files
    @property
    def program_files_x86(self) -> Path | None: return None
    @property
    def windows_apps(self) -> Path | None: return None
    def expand_env_vars(self, path: str) -> Path: return Path(path)

class MockFilesystemService(FilesystemService):
    def exists(self, path: Path) -> bool: return path.exists()
    def is_file(self, path: Path) -> bool: return path.is_file()
    def is_dir(self, path: Path) -> bool: return path.is_dir()
    def size(self, path: Path) -> int: return path.stat().st_size if path.exists() else 0
    def modified_time(self, path: Path) -> datetime: return datetime.now()
    def read_text(self, path: Path) -> str: return path.read_text(encoding="utf-8")

class MockClockService(ClockService):
    def now(self) -> datetime: return datetime.now()

class MockEnvironmentService(EnvironmentService):
    def get(self, key: str, default: str | None = None) -> str | None: return default
    def get_all(self) -> Mapping[str, str]: return {}

class MockPlatformServices(PlatformServices):
    def __init__(self, tmp_path: Path):
        self._paths = MockPathResolver(tmp_path)
        self._fs = MockFilesystemService()
        self._clock = MockClockService()
        self._env = MockEnvironmentService()
        
    @property
    def paths(self) -> PathResolver: return self._paths
    @property
    def fs(self) -> FilesystemService: return self._fs
    @property
    def clock(self) -> ClockService: return self._clock
    @property
    def env(self) -> EnvironmentService: return self._env


def test_pip_cache_detector(tmp_path: Path):
    resolver = MockPlatformServices(tmp_path)
    context = ScanContext(
        root_paths=(tmp_path,),
        settings=ScanSettings(),
        platform=Platform.WINDOWS,
        services=resolver,
        cancelled=lambda: False
    )
    
    # Create fake pip cache
    pip_cache = resolver.paths.local_app_data / "pip" / "cache"
    pip_cache.mkdir(parents=True)
    (pip_cache / "fake_package.whl").write_bytes(b"0" * 1024) # 1KB
    
    detector = PipCacheDetector()
    items = list(detector.detect(context))
    
    assert len(items) == 1
    item = items[0]
    assert item.size_bytes == 1024
    assert item.risk_level == RiskLevel.SAFE
    assert item.confidence == ConfidenceLevel.VERIFIED
    
    assert item.recommendation is not None
    assert item.recommendation.rollback == RollbackDifficulty.AUTOMATIC
    assert item.recommendation.command == "py -m pip cache purge"


def test_virtualenv_detector_orphaned(tmp_path: Path):
    resolver = MockPlatformServices(tmp_path)
    context = ScanContext(
        root_paths=(tmp_path,),
        settings=ScanSettings(),
        platform=Platform.WINDOWS,
        services=resolver,
        cancelled=lambda: False
    )
    
    # Create fake project with an orphaned venv
    project_dir = tmp_path / "my_project"
    venv_dir = project_dir / ".venv"
    venv_dir.mkdir(parents=True)
    
    cfg = venv_dir / "pyvenv.cfg"
    cfg.write_text("executable = C:\\Does\\Not\\Exist\\python.exe")
    
    detector = VirtualEnvDetector()
    items = list(detector.detect(context))
    
    assert len(items) == 1
    item = items[0]
    assert item.risk_level == RiskLevel.HIGH
    assert item.confidence == ConfidenceLevel.VERIFIED  # Verified orphan because base missing
    assert "no longer exists" in item.recommendation.explanation


def test_installation_detector_duplicates(tmp_path: Path):
    resolver = MockPlatformServices(tmp_path)
    context = ScanContext(
        root_paths=(tmp_path,),
        settings=ScanSettings(),
        platform=Platform.WINDOWS,
        services=resolver,
        cancelled=lambda: False
    )
    
    # Create a primary installation
    primary = resolver.paths.program_files / "Python" / "Python311"
    primary.mkdir(parents=True)
    (primary / "python.exe").touch()
    
    # Create a duplicate installation
    duplicate = resolver.paths.local_app_data / "Programs" / "Python" / "Python311"
    duplicate.mkdir(parents=True)
    (duplicate / "python.exe").touch()
    
    detector = InstallationDetector()
    items = list(detector.detect(context))
    
    assert len(items) == 2
    
    dupe_item = next(i for i in items if i.path == duplicate)
    primary_item = next(i for i in items if i.path == primary)
    
    assert dupe_item.is_reclaimable is True
    assert dupe_item.confidence == ConfidenceLevel.PROBABLE
    assert "duplicate" in dupe_item.recommendation.explanation.lower()
    
    assert primary_item.is_reclaimable is False
    assert primary_item.confidence == ConfidenceLevel.VERIFIED
