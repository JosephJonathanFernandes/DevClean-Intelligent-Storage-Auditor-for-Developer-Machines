import pytest
import time
from pathlib import Path
from devclean.infrastructure.cleanup.executor import CleanupExecutor
from devclean.domain.entities.cleanup_plan import CleanupPlan, CleanupAction
from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.entities.recommendation import Recommendation
from devclean.domain.entities.cleanup_decision import CleanupDecision
from devclean.domain.enums.category import Category
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel
from devclean.domain.enums.cleanup import CleanupOperation, RollbackStrategy, CleanupMode
from devclean.domain.enums.recommendation_reason import RecommendationReason
import uuid
import os

def create_action(path: Path) -> CleanupAction:
    item = AuditItem(
        path=path, size_bytes=100, category=Category.SYSTEM_CACHE,
        risk_level=RiskLevel.SAFE, description="safe", confidence=ConfidenceLevel.VERIFIED
    )
    rec = CleanupDecision(
        item=item,
        recommendation=Recommendation("Clean", "Expl", "Safe", RollbackStrategy.REGENERATES_AUTOMATICALLY, CleanupOperation.DELETE_DIRECTORY, files_affected=(path,)),
        priority_score=10.0,
        reason=RecommendationReason.STALE_CACHE
    )
    return CleanupAction(
        id=uuid.uuid4(), decision=rec, requires_confirmation=False
    )

def test_executor_handles_file_locks(tmp_path: Path):
    executor = CleanupExecutor(allowed_roots=(tmp_path,))
    
    target_dir = tmp_path / "locked_dir"
    target_dir.mkdir()
    target_file = target_dir / "file.txt"
    target_file.write_text("hello")
    
    action = create_action(target_dir)
    plan = CleanupPlan(id=uuid.uuid4(), actions=(action,), estimated_reclaimable_bytes=100, risk_summary={})
    
    # Open the file to lock it (Windows locks files opened for writing/reading without sharing)
    with open(target_file, "r") as f:
        # File is now locked. Cleanup should fail with PermissionError or OS Error.
        report = executor.execute(plan, mode=CleanupMode.EXECUTE)
        
    assert report.failed == 1
    assert report.succeeded == 0
    assert "Permission denied" in report.results[0].error or "OS error" in report.results[0].error


def test_executor_partial_failures(tmp_path: Path):
    executor = CleanupExecutor(allowed_roots=(tmp_path,))
    
    dir1 = tmp_path / "dir1"
    dir1.mkdir()
    
    dir2 = tmp_path / "locked_dir2"
    dir2.mkdir()
    file2 = dir2 / "file.txt"
    file2.write_text("hello")
    
    dir3 = tmp_path / "dir3"
    dir3.mkdir()
    
    actions = (create_action(dir1), create_action(dir2), create_action(dir3))
    plan = CleanupPlan(id=uuid.uuid4(), actions=actions, estimated_reclaimable_bytes=300, risk_summary={})
    
    with open(file2, "r") as f:
        report = executor.execute(plan, mode=CleanupMode.EXECUTE)
        
    assert report.succeeded == 2
    assert report.failed == 1
    
    assert not dir1.exists()
    assert dir2.exists()
    assert not dir3.exists()
