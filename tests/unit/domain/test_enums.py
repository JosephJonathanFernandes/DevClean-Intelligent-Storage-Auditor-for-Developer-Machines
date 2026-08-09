from devclean.domain.enums.category import Category
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel
from devclean.domain.enums.rollback_difficulty import RollbackDifficulty
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
    assert RollbackDifficulty.AUTOMATIC.value == "automatic"
    assert RollbackDifficulty.EASY.value == "easy"
    assert RollbackDifficulty.MANUAL.value == "manual"
    assert RollbackDifficulty.DIFFICULT.value == "difficult"
    assert RollbackDifficulty.IMPOSSIBLE.value == "impossible"

def test_platform_values():
    assert Platform.WINDOWS.value == "windows"
    assert Platform.LINUX.value == "linux"
    assert Platform.MACOS.value == "macos"
