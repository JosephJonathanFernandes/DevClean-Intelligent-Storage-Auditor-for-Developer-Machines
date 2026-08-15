from dataclasses import dataclass
from typing import Tuple, Dict, List
from collections import defaultdict

from devclean.domain.entities.cleanup_plan import CleanupPlan, CleanupAction
from devclean.domain.enums.category import Category


@dataclass(frozen=True)
class CleanupPreview:
    """A human-readable, trust-building summary of a cleanup execution."""
    category_name: str
    estimated_reclaim: int
    files_affected: int
    directories_affected: int
    rollback_strategy: str
    safety_reasons: Tuple[str, ...]
    confidence_levels: Tuple[str, ...]
    warnings: Tuple[str, ...]
    required_permissions: Tuple[str, ...]


class ExplainabilityService:
    """Analyzes a CleanupPlan to generate transparent previews."""
    
    def generate_previews(self, plan: CleanupPlan) -> List[CleanupPreview]:
        grouped_actions: Dict[Category, List[CleanupAction]] = defaultdict(list)
        for action in plan.actions:
            grouped_actions[action.decision.item.category].append(action)
            
        previews = []
        for category, actions in grouped_actions.items():
            estimated_reclaim = sum(a.decision.item.size_bytes for a in actions)
            
            # Count affected
            files_affected = 0
            dirs_affected = 0
            for a in actions:
                for p in a.decision.recommendation.files_affected:
                    if p.is_dir():
                        dirs_affected += 1
                    else:
                        files_affected += 1
                        
            # Aggregate metadata
            strategies = {a.decision.recommendation.rollback.value for a in actions}
            safety_reasons = {a.decision.recommendation.safety_reason for a in actions if a.decision.recommendation}
            confidences = {a.decision.item.confidence.value for a in actions}
            
            warnings = []
            if any(a.requires_confirmation for a in actions):
                warnings.append("Requires explicit user confirmation.")
            
            req_perms = set()
            for a in actions:
                if a.decision.recommendation.permissions.requires_admin:
                    req_perms.add("Administrator / sudo")
                req_perms.update(a.decision.recommendation.permissions.requires_process_shutdown)
            
            preview = CleanupPreview(
                category_name=category.value.replace("_", " ").title(),
                estimated_reclaim=estimated_reclaim,
                files_affected=files_affected,
                directories_affected=dirs_affected,
                rollback_strategy=", ".join(sorted(strategies)),
                safety_reasons=tuple(sorted(safety_reasons)),
                confidence_levels=tuple(sorted(confidences)),
                warnings=tuple(warnings),
                required_permissions=tuple(sorted(req_perms))
            )
            previews.append(preview)
            
        return sorted(previews, key=lambda p: p.estimated_reclaim, reverse=True)
