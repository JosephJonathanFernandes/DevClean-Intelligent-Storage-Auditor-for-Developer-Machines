from dataclasses import dataclass

@dataclass(frozen=True)
class AnalyzerResult:
    """
    Summary of an analyzer's execution.
    Note: Does NOT contain the discovered items to remain memory-efficient for streaming.
    """
    analyzer_name: str
    item_count: int
    total_size_bytes: int
    duration_seconds: float
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    
    @property
    def is_success(self) -> bool:
        return len(self.errors) == 0
