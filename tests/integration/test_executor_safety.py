import pytest
from pathlib import Path
from devclean.infrastructure.cleanup.executor import CleanupExecutor, AllowedRootPolicy
from devclean.domain.entities.cleanup_plan import CleanupPlan, CleanupAction
from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.entities.recommendation import Recommendation
from devclean.domain.entities.cleanup_recommendation import CleanupRecommendation
from devclean.domain.enums.category import Category
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel
from devclean.domain.enums.cleanup import CleanupOperation, RollbackStrategy, CleanupMode
from devclean.domain.enums.recommendation_reason import RecommendationReason
import uuid

def test_path_confinement_allows_safe_paths(tmp_path: Path):
    policy = AllowedRootPolicy((tmp_path,))
    assert policy.is_allowed(tmp_path / "safe_dir" / "file.txt")

def test_path_confinement_rejects_outside_paths(tmp_path: Path):
    policy = AllowedRootPolicy((tmp_path,))
    outside_path = tmp_path.parent / "unsafe.txt"
    assert not policy.is_allowed(outside_path)

def test_executor_validation_fails_on_unsafe_path(tmp_path: Path):
    executor = CleanupExecutor(allowed_roots=(tmp_path,))
    
    unsafe_path = tmp_path.parent / "unsafe_dir"
    
    item = AuditItem(
        path=unsafe_path, size_bytes=100, category=Category.SYSTEM_CACHE,
        risk_level=RiskLevel.SAFE, description="safe", confidence=ConfidenceLevel.VERIFIED
    )
    rec = CleanupRecommendation(
        item=item,
        recommendation=Recommendation("Clean", "Expl", "Safe", RollbackStrategy.REGENERATES_AUTOMATICALLY, CleanupOperation.DELETE_DIRECTORY, files_affected=(unsafe_path,)),
        priority_score=10.0,
        reason=RecommendationReason.STALE_CACHE
    )
    
    action = CleanupAction(
        id=uuid.uuid4(), decision=rec, requires_confirmation=False
    )
    
    plan = CleanupPlan(id=uuid.uuid4(), actions=(action,), estimated_reclaimable_bytes=100, risk_summary={})
    
    report = executor.execute(plan, mode=CleanupMode.EXECUTE)
    assert report.failed == 1
    assert report.succeeded == 0
    # Because validation failed, no execution happened.
    assert len(report.results) == 0

def test_executor_idempotency(tmp_path: Path):
    executor = CleanupExecutor(allowed_roots=(tmp_path,))
    missing_dir = tmp_path / "missing"
    
    item = AuditItem(
        path=missing_dir, size_bytes=100, category=Category.SYSTEM_CACHE,
        risk_level=RiskLevel.SAFE, description="safe", confidence=ConfidenceLevel.VERIFIED
    )
    rec = CleanupRecommendation(
        item=item,
        recommendation=Recommendation("Clean", "Expl", "Safe", RollbackStrategy.REGENERATES_AUTOMATICALLY, CleanupOperation.DELETE_DIRECTORY, files_affected=(missing_dir,)),
        priority_score=10.0,
        reason=RecommendationReason.STALE_CACHE
    )
    
    action = CleanupAction(
        id=uuid.uuid4(), decision=rec, requires_confirmation=False
    )
    
    plan = CleanupPlan(id=uuid.uuid4(), actions=(action,), estimated_reclaimable_bytes=100, risk_summary={})
    
    # Missing directory -> success
    report = executor.execute(plan, mode=CleanupMode.EXECUTE)
    assert report.succeeded == 1
    assert report.failed == 0
