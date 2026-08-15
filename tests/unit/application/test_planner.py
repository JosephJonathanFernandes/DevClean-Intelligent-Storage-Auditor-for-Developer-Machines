import pytest
from pathlib import Path

from devclean.application.cleanup.planner import CleanupPlanner
from devclean.domain.entities.cleanup_policy import ConservativePolicy, BalancedPolicy
from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.entities.recommendation import Recommendation
from devclean.domain.entities.cleanup_recommendation import CleanupRecommendation
from devclean.domain.enums.category import Category
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel
from devclean.domain.enums.cleanup import CleanupOperation, RollbackStrategy
from devclean.domain.enums.recommendation_reason import RecommendationReason


def test_planner_respects_policies():
    safe_item = AuditItem(
        path=Path("/safe"), size_bytes=100, category=Category.SYSTEM_CACHE,
        risk_level=RiskLevel.SAFE, description="safe", confidence=ConfidenceLevel.VERIFIED,
        is_reclaimable=True
    )
    safe_rec = CleanupRecommendation(
        item=safe_item,
        recommendation=Recommendation("Clean", "Expl", "Safe", RollbackStrategy.REGENERATES_AUTOMATICALLY, CleanupOperation.PURGE_CACHE),
        priority_score=10.0,
        reason=RecommendationReason.STALE_CACHE
    )
    
    low_item = AuditItem(
        path=Path("/low"), size_bytes=100, category=Category.VENV,
        risk_level=RiskLevel.LOW, description="low", confidence=ConfidenceLevel.VERIFIED,
        is_reclaimable=True
    )
    low_rec = CleanupRecommendation(
        item=low_item,
        recommendation=Recommendation("Clean", "Expl", "Safe", RollbackStrategy.REQUIRES_MANUAL_RESTORE, CleanupOperation.DELETE_DIRECTORY),
        priority_score=5.0,
        reason=RecommendationReason.UNUSED_ENVIRONMENT
    )
    
    planner = CleanupPlanner()
    
    # Conservative should only plan safe_item
    plan1 = planner.create_plan([safe_rec, low_rec], ConservativePolicy)
    assert len(plan1.actions) == 1
    assert plan1.actions[0].decision == safe_rec
    
    # Balanced should plan both
    plan2 = planner.create_plan([safe_rec, low_rec], BalancedPolicy)
    assert len(plan2.actions) == 2


def test_planner_skips_unreclaimable():
    unreclaimable_item = AuditItem(
        path=Path("/safe"), size_bytes=100, category=Category.SYSTEM_CACHE,
        risk_level=RiskLevel.SAFE, description="safe", confidence=ConfidenceLevel.VERIFIED,
        is_reclaimable=False
    )
    rec = CleanupRecommendation(
        item=unreclaimable_item,
        recommendation=Recommendation("Clean", "Expl", "Safe", RollbackStrategy.REGENERATES_AUTOMATICALLY, CleanupOperation.PURGE_CACHE),
        priority_score=10.0,
        reason=RecommendationReason.STALE_CACHE
    )
    
    planner = CleanupPlanner()
    
    plan = planner.create_plan([rec], ConservativePolicy)
    assert len(plan.actions) == 0
