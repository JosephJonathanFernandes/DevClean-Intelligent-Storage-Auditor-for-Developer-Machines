import pytest
from pathlib import Path
from devclean.application.cleanup.planner import CleanupPlanner
from devclean.domain.entities.cleanup_policy import BalancedPolicy
from devclean.domain.entities.audit_report import AuditReport
from devclean.domain.entities.scan_summary import ScanSummary
from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.entities.recommendation import Recommendation
from devclean.domain.enums.category import Category
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel
from devclean.domain.enums.cleanup import CleanupOperation, RollbackStrategy


def test_planner_performance(benchmark):
    # Create a large report (e.g., 10,000 items)
    items = []
    for i in range(10000):
        items.append(AuditItem(
            path=Path(f"/fake/path/{i}"), size_bytes=1024, category=Category.SYSTEM_CACHE,
            risk_level=RiskLevel.SAFE if i % 2 == 0 else RiskLevel.MODERATE,
            description="fake", confidence=ConfidenceLevel.VERIFIED,
            recommendation=Recommendation("Clean", "Expl", "Safe", RollbackStrategy.REGENERATES_AUTOMATICALLY, CleanupOperation.DELETE_DIRECTORY)
        ))
        
    report = AuditReport(summary=ScanSummary(0, 0, {}), items=tuple(items))
    planner = CleanupPlanner()
    
    plan = benchmark(planner.create_plan, report, BalancedPolicy)
    
    # 5000 items should be SAFE, other 5000 are MODERATE. Balanced Policy allows SAFE and LOW.
    assert len(plan.actions) == 5000
