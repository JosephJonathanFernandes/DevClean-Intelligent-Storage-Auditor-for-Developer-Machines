from dataclasses import dataclass
from typing import FrozenSet

from devclean.domain.enums.risk_level import RiskLevel

@dataclass(frozen=True)
class CleanupPolicy:
    """Models different risk tolerances for automated cleanup."""
    name: str
    allowed_risks: FrozenSet[RiskLevel]
    require_confirmation_for_risks: FrozenSet[RiskLevel]

# Predefined immutable singletons
ConservativePolicy = CleanupPolicy(
    name="Conservative",
    allowed_risks=frozenset([RiskLevel.SAFE]),
    require_confirmation_for_risks=frozenset([RiskLevel.SAFE])
)

BalancedPolicy = CleanupPolicy(
    name="Balanced",
    allowed_risks=frozenset([RiskLevel.SAFE, RiskLevel.LOW]),
    require_confirmation_for_risks=frozenset([RiskLevel.LOW])
)

AggressivePolicy = CleanupPolicy(
    name="Aggressive",
    allowed_risks=frozenset([RiskLevel.SAFE, RiskLevel.LOW, RiskLevel.MODERATE]),
    require_confirmation_for_risks=frozenset([RiskLevel.MODERATE])
)
