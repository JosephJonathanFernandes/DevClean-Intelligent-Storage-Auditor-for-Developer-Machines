import pytest
from pathlib import Path

from devclean.domain.entities.scan_context import ScanContext, ScanSettings
from devclean.domain.enums.platform import Platform
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel
from devclean.infrastructure.chrome.detectors.ai_models import ChromeAIModelDetector
from devclean.infrastructure.chrome.detectors.cache import ChromeCacheDetector
from devclean.infrastructure.chrome.detectors.profiles import ChromeProfileDetector

from tests.unit.infrastructure.test_python_detectors import MockPlatformServices


def test_chrome_ai_model_detector(tmp_path: Path):
    resolver = MockPlatformServices(tmp_path)
    context = ScanContext(
        root_paths=(tmp_path,),
        settings=ScanSettings(),
        platform=Platform.WINDOWS,
        services=resolver,
        cancelled=lambda: False
    )
    
    # Create fake AI model directory
    chrome_dir = resolver.paths.local_app_data / "Google" / "Chrome" / "User Data"
    model_dir = chrome_dir / "OptGuideOnDeviceModel"
    model_dir.mkdir(parents=True)
    (model_dir / "model.tflite").write_bytes(b"0" * 2048) # 2KB
    
    # And a different pattern
    prediction_dir = chrome_dir / "OptimizationGuidePredictorModels"
    prediction_dir.mkdir(parents=True)
    
    detector = ChromeAIModelDetector()
    items = list(detector.detect(context))
    
    assert len(items) == 2
    for item in items:
        assert item.risk_level == RiskLevel.LOW
        assert item.confidence == ConfidenceLevel.VERIFIED
        assert item.is_reclaimable is True


def test_chrome_profile_detector(tmp_path: Path):
    resolver = MockPlatformServices(tmp_path)
    context = ScanContext(
        root_paths=(tmp_path,),
        settings=ScanSettings(),
        platform=Platform.WINDOWS,
        services=resolver,
        cancelled=lambda: False
    )
    
    chrome_dir = resolver.paths.local_app_data / "Google" / "Chrome" / "User Data"
    default_profile = chrome_dir / "Default"
    default_profile.mkdir(parents=True)
    
    profile_1 = chrome_dir / "Profile 1"
    profile_1.mkdir(parents=True)
    
    detector = ChromeProfileDetector()
    items = list(detector.detect(context))
    
    assert len(items) == 2
    for item in items:
        assert item.risk_level == RiskLevel.HIGH
        assert item.is_reclaimable is False  # Profiles shouldn't be recommended for deletion by default


def test_chrome_cache_detector(tmp_path: Path):
    resolver = MockPlatformServices(tmp_path)
    context = ScanContext(
        root_paths=(tmp_path,),
        settings=ScanSettings(),
        platform=Platform.WINDOWS,
        services=resolver,
        cancelled=lambda: False
    )
    
    chrome_dir = resolver.paths.local_app_data / "Google" / "Chrome" / "User Data"
    cache_dir = chrome_dir / "Default" / "Cache"
    cache_dir.mkdir(parents=True)
    (cache_dir / "data_1").touch()
    
    gpu_cache_dir = chrome_dir / "Profile 1" / "GPUCache"
    gpu_cache_dir.mkdir(parents=True)
    
    detector = ChromeCacheDetector()
    items = list(detector.detect(context))
    
    assert len(items) == 2
    for item in items:
        assert item.risk_level == RiskLevel.SAFE
        assert item.is_reclaimable is True
