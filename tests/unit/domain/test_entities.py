import pytest
from pathlib import Path
from dataclasses import FrozenInstanceError

from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.entities.recommendation import Recommendation
from devclean.domain.entities.audit_report import AuditReport
from devclean.domain.entities.scan_summary import ScanSummary
from devclean.domain.enums.category import Category
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel
from devclean.domain.enums.cleanup import RollbackStrategy, CleanupOperation

def test_audit_item_immutability():
    item = AuditItem(
        path=Path("/test/path"),
        size_bytes=100,
        category=Category.UNKNOWN,
        risk_level=RiskLevel.SAFE,
        description="Test Item",
        confidence=ConfidenceLevel.VERIFIED
    )
    
    with pytest.raises(FrozenInstanceError):
        item.size_bytes = 200 # type: ignore

def test_audit_item_hashing():
    import uuid
    shared_id = uuid.uuid4()
    item1 = AuditItem(
        path=Path("/test/path"),
        size_bytes=100,
        category=Category.UNKNOWN,
        risk_level=RiskLevel.SAFE,
        description="Test Item",
        confidence=ConfidenceLevel.VERIFIED,
        id=shared_id
    )
    item2 = AuditItem(
        path=Path("/test/path"),
        size_bytes=100,
        category=Category.UNKNOWN,
        risk_level=RiskLevel.SAFE,
        description="Test Item",
        confidence=ConfidenceLevel.VERIFIED,
        id=shared_id
    )
    
    assert hash(item1) == hash(item2)
    assert item1 == item2

def test_recommendation_serialization():
    rec = Recommendation(
        title="Delete me",
        explanation="It is bad",
        safety_reason="Nothing will break",
        operation=CleanupOperation.DELETE_DIRECTORY, rollback=RollbackStrategy.REGENERATES_AUTOMATICALLY
    )
    
    assert rec.rollback == RollbackStrategy.REGENERATES_AUTOMATICALLY
    assert rec.rollback.value == "regenerates_automatically"

def test_audit_report_properties():
    item1 = AuditItem(
        path=Path("/test/path1"),
        size_bytes=100,
        category=Category.UNKNOWN,
        risk_level=RiskLevel.HIGH,
        description="Test Item 1",
        confidence=ConfidenceLevel.VERIFIED,
        is_reclaimable=True
    )
    item2 = AuditItem(
        path=Path("/test/path2"),
        size_bytes=50,
        category=Category.UNKNOWN,
        risk_level=RiskLevel.LOW,
        description="Test Item 2",
        confidence=ConfidenceLevel.PROBABLE,
        is_reclaimable=False
    )
    
    summary = ScanSummary(
        total_items=2,
        total_size_bytes=150,
        reclaimable_size_bytes=100
    )
    
    report = AuditReport(items=(item1, item2), summary=summary)
    
    assert len(report.items) == 2
    assert report.summary.total_size_bytes == 150
    assert report.summary.reclaimable_size_bytes == 100
    assert report.id is not None # UUID generation works
