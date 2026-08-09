import pytest
from pathlib import Path
from datetime import datetime

from devclean.domain.entities.scan_context import ScanContext
from devclean.domain.services.analyzer import Analyzer
from devclean.domain.entities.audit_item import AuditItem

class AnalyzerContractTestSuite:
    """
    A reusable test suite that enforces the contract for all DevClean Analyzers.
    Any new analyzer must inherit this class and provide a configured analyzer instance.
    """

    @pytest.fixture
    def analyzer(self) -> Analyzer:
        """Subclasses must override to return the configured analyzer."""
        raise NotImplementedError

    @pytest.fixture
    def context(self) -> ScanContext:
        """Subclasses must override to return a mock context."""
        raise NotImplementedError

    @pytest.fixture
    def mock_fs_hash(self, context: ScanContext) -> int:
        """Hashes the mock filesystem before the scan to verify no mutation."""
        # Simple heuristic: sum sizes of all files in tmp_path
        total = 0
        root = context.root_paths[0]
        for item in root.rglob("*"):
            if item.is_file():
                total += item.stat().st_size
        return total

    def test_analyzer_is_side_effect_free(self, analyzer: Analyzer, context: ScanContext, mock_fs_hash: int):
        """Analyzers must not mutate the filesystem."""
        list(analyzer.scan(context))
        
        post_scan_hash = 0
        root = context.root_paths[0]
        for item in root.rglob("*"):
            if item.is_file():
                post_scan_hash += item.stat().st_size
                
        assert mock_fs_hash == post_scan_hash, f"{analyzer.metadata.name} mutated the filesystem!"

    def test_deterministic_sorting(self, analyzer: Analyzer, context: ScanContext):
        """
        Analyzers must emit items in a deterministic order to ensure stable snapshots.
        Order is: (category.value, path, size descending)
        """
        items = list(analyzer.scan(context))
        
        sorted_items = sorted(
            items,
            key=lambda i: (i.category.value, str(i.path), -i.size_bytes)
        )
        
        for idx, (actual, expected) in enumerate(zip(items, sorted_items)):
            assert actual == expected, f"Item at index {idx} out of order in {analyzer.metadata.name}"

    def test_explainability_compliance(self, analyzer: Analyzer, context: ScanContext):
        """All reclaimable items MUST have a Recommendation for safe explainability."""
        items = list(analyzer.scan(context))
        for item in items:
            if item.is_reclaimable:
                assert item.recommendation is not None, f"Reclaimable item {item.path} missing recommendation"
                assert len(item.recommendation.title) > 0
                assert len(item.recommendation.explanation) > 0


