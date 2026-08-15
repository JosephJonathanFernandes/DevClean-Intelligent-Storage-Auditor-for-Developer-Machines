import uuid
from pathlib import Path

from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.entities.audit_report import AuditReport
from devclean.domain.entities.scan_summary import ScanSummary
from devclean.domain.entities.recommendation_context import RecommendationContext
from devclean.domain.enums.category import Category
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel
from devclean.application.cleanup.recommendation_engine import RecommendationEngine

def test_recommendation_engine_stability():
    """
    Test that recommendation ordering, scores, and explanations are deterministic.
    Given the same input report, the engine should always produce the exact same
    CleanupDecisions in the exact same order.
    """
    engine = RecommendationEngine()
    
    # Create a mixed bag of items
    items = [
        AuditItem(
            id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            path=Path("/dummy/pip/cache"),
            size_bytes=500_000,
            category=Category.PYTHON_CACHE,
            risk_level=RiskLevel.SAFE,
            description="Pip cache",
            confidence=ConfidenceLevel.VERIFIED,
            is_reclaimable=True
        ),
        AuditItem(
            id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
            path=Path("/dummy/large_safe"),
            size_bytes=2_000_000_000, # 2 GB
            category=Category.UNKNOWN,
            risk_level=RiskLevel.SAFE,
            description="Large safe file",
            confidence=ConfidenceLevel.VERIFIED,
            is_reclaimable=True
        ),
        AuditItem(
            id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
            path=Path("/dummy/venv"),
            size_bytes=100_000_000,
            category=Category.VENV,
            risk_level=RiskLevel.HIGH,
            description="Venv",
            confidence=ConfidenceLevel.PROBABLE,
            is_reclaimable=True
        )
    ]
    
    report = AuditReport(
        items=tuple(items),
        summary=ScanSummary(total_items=3, total_size_bytes=2_100_500_000, reclaimable_size_bytes=2_100_500_000)
    )
    
    context = RecommendationContext(
        free_disk_bytes=5_000_000_000,
        total_disk_bytes=100_000_000_000,
        user_policy="balanced"
    )
    
    # Run twice
    run1 = engine.generate_recommendations(report, context)
    run2 = engine.generate_recommendations(report, context)
    
    # Order must be deterministic
    assert [r.item.id for r in run1] == [r.item.id for r in run2]
    
    # Scores must be deterministic
    assert [r.priority_score for r in run1] == [r.priority_score for r in run2]
    
    # Explanations must be deterministic
    assert [r.recommendation.explanation for r in run1] == [r.recommendation.explanation for r in run2]
    
    # Check that disk pressure rule applies correctly
    # context is under 10% free disk space (5GB free out of 100GB total)
    # The Large Safe file should have a massive score boost (20.0 bonus)
    large_safe_rec = next(r for r in run1 if r.item.id == uuid.UUID("22222222-2222-2222-2222-222222222222"))
    assert large_safe_rec.priority_score > 25.0
    assert large_safe_rec.reason.value == "high_disk_pressure"
    
    # Check that breakdown exists and contains expected keys
    assert "safety" in large_safe_rec.score_breakdown
    assert "size" in large_safe_rec.score_breakdown
    assert "disk_pressure" in large_safe_rec.score_breakdown
