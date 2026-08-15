import uuid
from typing import Dict, Sequence
from devclean.domain.entities.cleanup_decision import CleanupDecision
from devclean.domain.entities.cleanup_policy import CleanupPolicy
from devclean.domain.entities.cleanup_plan import CleanupPlan, CleanupAction
from devclean.domain.enums.risk_level import RiskLevel

class CleanupPlanner:
    """Evaluates an AuditReport against a CleanupPolicy to generate a transactional CleanupPlan."""
    
    def create_plan(self, decisions: Sequence[CleanupDecision], policy: CleanupPolicy) -> CleanupPlan:
        actions = []
        estimated_reclaimable = 0
        risk_summary: Dict[RiskLevel, int] = {
            RiskLevel.SAFE: 0,
            RiskLevel.LOW: 0,
            RiskLevel.MODERATE: 0,
            RiskLevel.HIGH: 0
        }
        
        for decision in decisions:
            item = decision.item
            # Skip items that are not reclaimable (locked, etc.)
            if not item.is_reclaimable:
                continue
                
            # Skip items outside the allowed policy risk
            if item.risk_level not in policy.allowed_risks:
                continue
                
            # Check if confirmation is required
            requires_confirmation = item.risk_level in policy.require_confirmation_for_risks
            
            action = CleanupAction(
                id=uuid.uuid4(),
                decision=decision,
                requires_confirmation=requires_confirmation
            )
            
            actions.append(action)
            estimated_reclaimable += item.size_bytes
            risk_summary[item.risk_level] += 1
            
        return CleanupPlan(
            id=uuid.uuid4(),
            actions=tuple(actions),
            estimated_reclaimable_bytes=estimated_reclaimable,
            risk_summary=risk_summary
        )
