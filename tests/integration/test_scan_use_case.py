import pytest
from pathlib import Path
from dataclasses import asdict
import json

from devclean.domain.entities.scan_context import ScanContext, ScanSettings
from devclean.domain.enums.platform import Platform
from devclean.application.analyzers.registry import AnalyzerRegistry
from devclean.application.events.event_bus import EventBus
from devclean.application.analyzers.pipeline import AnalyzerPipeline
from devclean.application.use_cases.scan import ScanUseCase
from devclean.infrastructure.python.analyzer import PythonAnalyzer
from devclean.infrastructure.chrome.analyzer import ChromeAnalyzer

from tests.unit.infrastructure.test_python_detectors import MockPlatformServices

def test_full_scan_use_case_snapshot(tmp_path: Path, snapshot):
    resolver = MockPlatformServices(tmp_path)
    
    # 1. Setup predictable fake environment
    
    # Python Pip Cache
    pip_cache = resolver.paths.local_app_data / "pip" / "cache"
    pip_cache.mkdir(parents=True)
    (pip_cache / "fake.whl").write_bytes(b"A" * 500)
    
    # Python Duplicate Installs
    primary = resolver.paths.program_files / "Python" / "Python311"
    primary.mkdir(parents=True)
    (primary / "python.exe").touch()
    
    duplicate = resolver.paths.local_app_data / "Programs" / "Python" / "Python311"
    duplicate.mkdir(parents=True)
    (duplicate / "python.exe").touch()
    
    # Chrome AI Models
    chrome_dir = resolver.paths.local_app_data / "Google" / "Chrome" / "User Data"
    model_dir = chrome_dir / "OptGuideOnDeviceModel"
    model_dir.mkdir(parents=True)
    (model_dir / "model.tflite").write_bytes(b"B" * 200)
    
    # Docker Desktop WSL Backend
    docker_wsl_dir = resolver.paths.local_app_data / "Docker" / "wsl" / "data"
    docker_wsl_dir.mkdir(parents=True)
    (docker_wsl_dir / "ext4.vhdx").write_bytes(b"C" * 1000)
    
    # WSL Distros
    ubuntu_dir = resolver.paths.local_app_data / "Packages" / "CanonicalGroupLimited.Ubuntu_123" / "LocalState"
    ubuntu_dir.mkdir(parents=True)
    (ubuntu_dir / "ext4.vhdx").write_bytes(b"D" * 2000)
    
    # 2. Configure app
    registry = AnalyzerRegistry()
    registry.register(PythonAnalyzer())
    registry.register(ChromeAnalyzer())
    
    from devclean.infrastructure.docker.analyzer import DockerAnalyzer
    from devclean.infrastructure.wsl.analyzer import WSLAnalyzer
    registry.register(DockerAnalyzer())
    registry.register(WSLAnalyzer())
    
    registry.freeze()
    
    event_bus = EventBus()
    
    pipeline = AnalyzerPipeline(registry, event_bus)
    use_case = ScanUseCase(pipeline)
    
    context = ScanContext(
        root_paths=(tmp_path,),
        settings=ScanSettings(),
        platform=Platform.WINDOWS,
        services=resolver,
        cancelled=lambda: False
    )
    
    # 3. Execute
    result = use_case.execute(context)
    
    # 4. Serialize for snapshot
    # We remove non-deterministic fields like UUIDs and absolute paths containing tmp_path
    
    def sanitize_path(p: Path) -> str:
        return str(p).replace(str(tmp_path), "<TMP_PATH>").replace("\\", "/")
        
    def sanitize_item(item):
        d = asdict(item)
        d["path"] = sanitize_path(item.path)
        d["id"] = "<UUID>"
        if d.get("last_modified"):
            d["last_modified"] = "<TIMESTAMP>"
        for k, v in list(d["metadata"].items()):
            if isinstance(v, str) and str(tmp_path) in v:
                d["metadata"][k] = sanitize_path(Path(v))
        if item.recommendation and item.recommendation.files_affected:
            d["recommendation"]["files_affected"] = [sanitize_path(p) for p in item.recommendation.files_affected]
        if item.recommendation:
            d["recommendation"]["rollback"] = item.recommendation.rollback.value
        d["category"] = item.category.value
        d["risk_level"] = item.risk_level.value
        d["confidence"] = item.confidence.value
        return d
        
    report_data = {
        "summary": asdict(result.report.summary),
        "statistics": {
            k: v for k, v in asdict(result.statistics).items() 
            if k not in ("scan_duration_seconds",) # Duration is non-deterministic
        },
        # Sort items to ensure deterministic snapshot ordering
        "items": sorted([sanitize_item(i) for i in result.report.items], key=lambda x: x["path"]),
    }
    
    # Ensure it matches the golden snapshot
    assert json.dumps(report_data, indent=2, sort_keys=True) == snapshot
