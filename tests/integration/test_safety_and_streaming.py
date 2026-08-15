import pytest
import os
import hashlib
from pathlib import Path

from devclean.domain.entities.scan_context import ScanContext, ScanSettings
from devclean.domain.enums.platform import Platform
from devclean.application.analyzers.registry import AnalyzerRegistry
from devclean.application.events.event_bus import EventBus
from devclean.application.analyzers.pipeline import AnalyzerPipeline
from devclean.application.use_cases.scan import ScanUseCase
from devclean.infrastructure.python.analyzer import PythonAnalyzer

from tests.unit.infrastructure.test_python_detectors import MockPlatformServices

def hash_directory_state(directory: Path) -> dict[str, str]:
    """Creates a deterministic hash of all files and their modification times."""
    state = {}
    for root, _, files in os.walk(directory):
        for file in files:
            path = Path(root) / file
            stat = path.stat()
            state[str(path)] = f"{stat.st_size}_{stat.st_mtime}"
    return state

def test_mutation_safety_during_scan(tmp_path: Path):
    resolver = MockPlatformServices(tmp_path)
    
    # Create some mock python environments
    venv_dir = resolver.paths.local_app_data / "my_venv"
    venv_dir.mkdir(parents=True)
    (venv_dir / "pyvenv.cfg").write_text("executable = nothing")
    (venv_dir / "fake_lib.py").write_text("print('hello')")
    
    pip_cache = resolver.paths.local_app_data / "pip" / "cache"
    pip_cache.mkdir(parents=True)
    (pip_cache / "fake.whl").write_bytes(b"0" * 1024)
    
    # Hash the state BEFORE scan
    pre_scan_state = hash_directory_state(tmp_path)
    
    # Setup full application
    registry = AnalyzerRegistry()
    registry.register(PythonAnalyzer())
    registry.freeze()
    
    pipeline = AnalyzerPipeline(registry, EventBus())
    use_case = ScanUseCase(pipeline)
    
    context = ScanContext(
        root_paths=(tmp_path,),
        settings=ScanSettings(),
        platform=Platform.WINDOWS,
        services=resolver,
        cancelled=lambda: False
    )
    
    # Run the scan
    result = use_case.execute(context)
    
    # Hash the state AFTER scan
    post_scan_state = hash_directory_state(tmp_path)
    
    # Verify exact same files exist with exact same sizes and modification times
    assert pre_scan_state == post_scan_state
    
    # Verify the scan actually found things
    assert result.statistics.analyzers_run == 1
    assert result.report.summary.total_items > 0
