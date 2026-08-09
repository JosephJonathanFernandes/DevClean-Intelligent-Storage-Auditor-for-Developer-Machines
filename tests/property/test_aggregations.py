from pathlib import Path
from hypothesis import given, strategies as st

from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.enums.category import Category
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel
from devclean.application.reporting.builder import AuditReportBuilder

@st.composite
def audit_item_strategy(draw):
    size = draw(st.integers(min_value=0, max_value=1_000_000_000))
    is_reclaim = draw(st.booleans())
    
    return AuditItem(
        path=Path(f"/fake/{draw(st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'))}"),
        size_bytes=size,
        category=draw(st.sampled_from(list(Category))),
        risk_level=draw(st.sampled_from(list(RiskLevel))),
        description="Random Item",
        confidence=draw(st.sampled_from(list(ConfidenceLevel))),
        is_reclaimable=is_reclaim
    )

@given(st.lists(audit_item_strategy(), max_size=100))
def test_report_builder_invariants(items):
    builder = AuditReportBuilder()
    
    for item in items:
        builder.add_item(item)
        
    report = builder.build(duration_seconds=1.5)
    
    # Invariant 1: Total items count must match exactly
    assert report.summary.total_items == len(items)
    
    # Invariant 2: Total size is exact sum
    expected_total_size = sum(item.size_bytes for item in items)
    assert report.summary.total_size_bytes == expected_total_size
    
    # Invariant 3: Reclaimable size is exact sum of reclaimable items
    expected_reclaimable_size = sum(item.size_bytes for item in items if item.is_reclaimable)
    assert report.summary.reclaimable_size_bytes == expected_reclaimable_size
    
    # Invariant 4: Reclaimable size <= Total size
    assert report.summary.reclaimable_size_bytes <= report.summary.total_size_bytes
    
    # Invariant 5: Items tuple in report maintains same length as input
    assert len(report.items) == len(items)
