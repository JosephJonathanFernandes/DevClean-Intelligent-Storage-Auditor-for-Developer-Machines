import uuid
from pathlib import Path
from rich.console import Console

from devclean.presentation.cli.presenter import ConsolePresenter
from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.entities.audit_report import AuditReport
from devclean.domain.entities.scan_summary import ScanSummary
from devclean.domain.entities.cleanup_plan import CleanupPlan, CleanupAction
from devclean.domain.entities.cleanup_decision import CleanupDecision
from devclean.domain.entities.recommendation import Recommendation
from devclean.domain.enums.category import Category
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel
from devclean.domain.enums.cleanup import CleanupOperation, RollbackStrategy
from devclean.domain.enums.recommendation_reason import RecommendationReason

def test_show_scan_summary_snapshot(snapshot):
    console = Console(width=100, record=True, color_system=None) # Disable colors in raw text for consistent snapshotting
    presenter = ConsolePresenter(console=console)
    
    item = AuditItem(
        id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        path=Path("/test/cache"),
        size_bytes=10_000_000,
        category=Category.SYSTEM_CACHE,
        risk_level=RiskLevel.SAFE,
        description="System cache files",
        confidence=ConfidenceLevel.VERIFIED
    )
    
    report = AuditReport(
        items=(item,),
        summary=ScanSummary(total_items=1, total_size_bytes=10_000_000, reclaimable_size_bytes=10_000_000)
    )
    
    presenter.show_scan_summary(report)
    assert console.export_text() == snapshot


def test_show_cleanup_preview_snapshot(snapshot):
    console = Console(width=100, record=True, color_system=None)
    presenter = ConsolePresenter(console=console)
    
    item = AuditItem(
        id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        path=Path("/test/cache"),
        size_bytes=15_000_000,
        category=Category.SYSTEM_CACHE,
        risk_level=RiskLevel.SAFE,
        description="System cache files",
        confidence=ConfidenceLevel.VERIFIED
    )
    
    decision = CleanupDecision(
        item=item,
        recommendation=Recommendation("Clean", "Expl", "Safe", RollbackStrategy.REGENERATES_AUTOMATICALLY, CleanupOperation.PURGE_CACHE),
        priority_score=10.0,
        reason=RecommendationReason.STALE_CACHE
    )
    
    action = CleanupAction(
        id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        decision=decision,
        requires_confirmation=False
    )
    
    plan = CleanupPlan(
        id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
        actions=(action,),
        estimated_reclaimable_bytes=15_000_000,
        risk_summary={RiskLevel.SAFE: 1}
    )
    
    presenter.show_cleanup_preview(plan)
    assert console.export_text() == snapshot


def test_show_history_snapshot(snapshot):
    console = Console(width=100, record=True, color_system=None)
    presenter = ConsolePresenter(console=console)
    
    log_lines = [
        '{"event": "CLEANUP_EXECUTION_COMPLETED", "timestamp": "2026-08-15T10:22:00Z", "freed_bytes": 8100000000, "policy": "balanced", "mode": "EXECUTE"}',
        '{"event": "CLEANUP_EXECUTION_COMPLETED", "timestamp": "2026-08-12T18:03:00Z", "freed_bytes": 2400000000, "policy": "conservative", "mode": "EXECUTE"}'
    ]
    
    presenter.show_history(log_lines)
    assert console.export_text() == snapshot

def test_show_explanation_snapshot(snapshot):
    console = Console(width=100, record=True, color_system=None)
    presenter = ConsolePresenter(console=console)
    
    presenter.show_explanation("python-cache")
    assert console.export_text() == snapshot
