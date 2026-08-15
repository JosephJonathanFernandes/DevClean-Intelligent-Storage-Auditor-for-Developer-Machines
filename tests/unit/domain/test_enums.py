from devclean.domain.enums.category import Category
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel
from devclean.domain.enums.cleanup import RollbackStrategy
from devclean.domain.enums.platform import Platform

def test_risk_level_ordering():
    # Enums aren't strictly comparable by default in Python unless IntEnum is used,
    # but we can test their explicit existence and strings
    assert RiskLevel.SAFE.value == "safe"
    assert RiskLevel.LOW.value == "low"
    assert RiskLevel.MODERATE.value == "moderate"
    assert RiskLevel.HIGH.value == "high"

def test_confidence_level_values():
    assert ConfidenceLevel.VERIFIED.value == "verified"
    assert ConfidenceLevel.PROBABLE.value == "probable"
    assert ConfidenceLevel.HEURISTIC.value == "heuristic"
    assert ConfidenceLevel.UNKNOWN.value == "unknown"

def test_rollback_difficulty_values():
    assert RollbackStrategy.REGENERATES_AUTOMATICALLY.value == "regenerates_automatically"
    assert RollbackStrategy.REQUIRES_REDOWNLOAD.value == "requires_redownload"
    assert RollbackStrategy.REQUIRES_MANUAL_RESTORE.value == "requires_manual_restore"
    assert RollbackStrategy.ARCHIVE_AND_RESTORE.value == "archive_and_restore"
    assert RollbackStrategy.NO_ROLLBACK_AVAILABLE.value == "no_rollback_available"

def test_platform_values():
    assert Platform.WINDOWS.value == "windows"
    assert Platform.LINUX.value == "linux"
    assert Platform.MACOS.value == "macos"
