from typing import List, Sequence

from devclean.domain.entities.audit_report import AuditReport
from devclean.domain.entities.cleanup_decision import CleanupDecision
from devclean.domain.entities.recommendation_context import RecommendationContext
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.recommendation_reason import RecommendationReason
from devclean.application.cleanup.recommendation_rules import RecommendationRule, ALL_RULES, DefaultRule

class RecommendationEngine:
    def __init__(self, rules: Sequence[RecommendationRule] | None = None):
        self.rules = rules if rules is not None else ALL_RULES
        self.default_rule = DefaultRule()

    def generate_recommendations(
        self, 
        report: AuditReport, 
        context: RecommendationContext | None = None
    ) -> List[CleanupDecision]:
        """
        Processes a ScanResult and returns a list of prioritized CleanupDecisions.
        """
        results: List[CleanupDecision] = []
        
        for item in report.items:
            # Find the first matching rule
            rule_to_apply = self.default_rule
            for rule in self.rules:
                if rule.applies(item):
                    rule_to_apply = rule
                    break
                    
            # Compute recommendation
            rec = rule_to_apply.recommend(item)
            
            # Compute score
            base_score, breakdown = rule_to_apply.score(item)
            
            # Adjust score based on context (e.g. disk pressure)
            final_score = self._apply_context_modifiers(base_score, breakdown, item, context)
            
            # Compute reason
            reason = rule_to_apply.reason(item)
            
            # Provide high disk pressure reason if applicable
            if context and self._is_high_disk_pressure(context):
                reason = RecommendationReason.HIGH_DISK_PRESSURE
            
            results.append(CleanupDecision(
                item=item,
                recommendation=rec,
                priority_score=final_score,
                reason=reason,
                score_breakdown=breakdown
            ))
            
        # Sort by priority score descending
        results.sort(key=lambda r: r.priority_score, reverse=True)
        return results

    def _is_high_disk_pressure(self, context: RecommendationContext) -> bool:
        if context.total_disk_bytes == 0:
            return False
        free_ratio = context.free_disk_bytes / context.total_disk_bytes
        return free_ratio < 0.10 # Less than 10% free

    def _apply_context_modifiers(
        self, 
        base_score: float, 
        breakdown: dict[str, float],
        item: 'AuditItem', 
        context: RecommendationContext | None
    ) -> float:
        if not context:
            return base_score
            
        score = base_score
        
        if self._is_high_disk_pressure(context):
            # Prioritize large safe cleanups heavily
            if item.size_bytes > 500_000_000 and item.risk_level in (RiskLevel.SAFE, RiskLevel.LOW):
                modifier = 20.0
                score += modifier
                breakdown["disk_pressure"] = modifier
                
        return score
