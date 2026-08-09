import pytest
from pathlib import Path
from devclean.application.use_cases.scan import ScanUseCase
from devclean.application.analyzers.registry import AnalyzerRegistry
from devclean.application.analyzers.pipeline import AnalyzerPipeline
from devclean.application.events.event_bus import EventBus
from devclean.infrastructure.python.analyzer import PythonAnalyzer
from devclean.infrastructure.chrome.analyzer import ChromeAnalyzer
from devclean.infrastructure.docker.analyzer import DockerAnalyzer
from devclean.infrastructure.wsl.analyzer import WSLAnalyzer
from tests.unit.infrastructure.test_python_detectors import MockPlatformServices

# Mark all tests in this module with 'benchmark'
pytestmark = pytest.mark.benchmark

def test_full_scan_performance(benchmark, tmp_path: Path):
    """
    Benchmarks the performance of a full scan across all analyzers.
    Using pytest-benchmark to track timing.
    """
    resolver = MockPlatformServices(tmp_path)
    
    # 1. Populate a fake filesystem with large numbers of files to simulate a real machine
    
    # Python
    pip_cache = resolver.paths.local_app_data / "pip" / "cache"
    pip_cache.mkdir(parents=True)
    for i in range(100):
        (pip_cache / f"fake_{i}.whl").touch()
        
    conda_envs = resolver.paths.user_profile / "miniconda3" / "envs"
    conda_envs.mkdir(parents=True)
    for i in range(10):
        env = conda_envs / f"env_{i}"
        env.mkdir()
        (env / "python.exe").touch()

    # Chrome
    chrome_dir = resolver.paths.local_app_data / "Google" / "Chrome" / "User Data"
    model_dir = chrome_dir / "OptGuideOnDeviceModel"
    model_dir.mkdir(parents=True)
    (model_dir / "model.tflite").touch()
    
    # Docker
    docker_wsl_dir = resolver.paths.local_app_data / "Docker" / "wsl" / "data"
    docker_wsl_dir.mkdir(parents=True)
    (docker_wsl_dir / "ext4.vhdx").touch()
    
    # WSL
    ubuntu_dir = resolver.paths.local_app_data / "Packages" / "CanonicalGroupLimited.Ubuntu_123" / "LocalState"
    ubuntu_dir.mkdir(parents=True)
    (ubuntu_dir / "ext4.vhdx").touch()

    # 2. Configure app
    registry = AnalyzerRegistry()
    registry.register(PythonAnalyzer())
    registry.register(ChromeAnalyzer())
    registry.register(DockerAnalyzer())
    registry.register(WSLAnalyzer())
    
    event_bus = EventBus()
    pipeline = AnalyzerPipeline(registry, event_bus)
    use_case = ScanUseCase(pipeline)
    
    from devclean.domain.entities.scan_context import ScanContext, ScanSettings
    from devclean.domain.enums.platform import Platform
    
    context = ScanContext(
        root_paths=(tmp_path,),
        settings=ScanSettings(),
        platform=Platform.WINDOWS,
        services=resolver,
        cancelled=lambda: False
    )
    
    def run_scan():
        return use_case.execute(context)

    # 3. Benchmark the scan
    result = benchmark(run_scan)
    assert len(result.report.items) > 0
