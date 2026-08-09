import pytest
from pathlib import Path
from devclean.domain.entities.scan_context import ScanContext, ScanSettings
from devclean.domain.enums.platform import Platform
from devclean.domain.services.analyzer import Analyzer
from devclean.infrastructure.python.analyzer import PythonAnalyzer
from devclean.infrastructure.chrome.analyzer import ChromeAnalyzer
from devclean.infrastructure.docker.analyzer import DockerAnalyzer
from devclean.infrastructure.wsl.analyzer import WSLAnalyzer
from tests.unit.infrastructure.test_python_detectors import MockPlatformServices
from tests.unit.infrastructure.analyzer_contract import AnalyzerContractTestSuite

class TestPythonAnalyzerContract(AnalyzerContractTestSuite):
    @pytest.fixture
    def analyzer(self) -> Analyzer:
        return PythonAnalyzer()

    @pytest.fixture
    def context(self, tmp_path: Path) -> ScanContext:
        resolver = MockPlatformServices(tmp_path)
        # Setup fake python env
        pip_cache = resolver.paths.local_app_data / "pip" / "cache"
        pip_cache.mkdir(parents=True)
        (pip_cache / "fake.whl").touch()
        return ScanContext(root_paths=(tmp_path,), settings=ScanSettings(), platform=Platform.WINDOWS, services=resolver, cancelled=lambda: False)

class TestChromeAnalyzerContract(AnalyzerContractTestSuite):
    @pytest.fixture
    def analyzer(self) -> Analyzer:
        return ChromeAnalyzer()

    @pytest.fixture
    def context(self, tmp_path: Path) -> ScanContext:
        resolver = MockPlatformServices(tmp_path)
        chrome_dir = resolver.paths.local_app_data / "Google" / "Chrome" / "User Data"
        model_dir = chrome_dir / "OptGuideOnDeviceModel"
        model_dir.mkdir(parents=True)
        (model_dir / "model.tflite").touch()
        return ScanContext(root_paths=(tmp_path,), settings=ScanSettings(), platform=Platform.WINDOWS, services=resolver, cancelled=lambda: False)

class TestDockerAnalyzerContract(AnalyzerContractTestSuite):
    @pytest.fixture
    def analyzer(self) -> Analyzer:
        return DockerAnalyzer()

    @pytest.fixture
    def context(self, tmp_path: Path) -> ScanContext:
        resolver = MockPlatformServices(tmp_path)
        docker_wsl_dir = resolver.paths.local_app_data / "Docker" / "wsl" / "data"
        docker_wsl_dir.mkdir(parents=True)
        (docker_wsl_dir / "ext4.vhdx").touch()
        return ScanContext(root_paths=(tmp_path,), settings=ScanSettings(), platform=Platform.WINDOWS, services=resolver, cancelled=lambda: False)

class TestWSLAnalyzerContract(AnalyzerContractTestSuite):
    @pytest.fixture
    def analyzer(self) -> Analyzer:
        return WSLAnalyzer()

    @pytest.fixture
    def context(self, tmp_path: Path) -> ScanContext:
        resolver = MockPlatformServices(tmp_path)
        ubuntu_dir = resolver.paths.local_app_data / "Packages" / "CanonicalGroupLimited.Ubuntu_123" / "LocalState"
        ubuntu_dir.mkdir(parents=True)
        (ubuntu_dir / "ext4.vhdx").touch()
        return ScanContext(root_paths=(tmp_path,), settings=ScanSettings(), platform=Platform.WINDOWS, services=resolver, cancelled=lambda: False)
