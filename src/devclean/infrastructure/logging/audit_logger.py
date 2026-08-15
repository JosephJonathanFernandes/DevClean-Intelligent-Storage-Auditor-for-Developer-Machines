import json
import hashlib
import platform
import datetime
from pathlib import Path
from typing import Dict, Any

from devclean.domain.entities.cleanup_plan import CleanupPlan
from devclean.domain.entities.cleanup_result import CleanupExecutionReport
from devclean.domain.enums.cleanup import CleanupMode

class ExecutionHistoryLogger:
    """Logs cleanup executions securely to ~/.devclean/history."""
    
    def __init__(self, history_dir: Path | None = None):
        if history_dir is None:
            self.history_dir = Path.home() / ".devclean" / "history"
        else:
            self.history_dir = history_dir
            
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
    def log_execution(
        self, 
        plan: CleanupPlan, 
        report: CleanupExecutionReport, 
        mode: CleanupMode, 
        policy_name: str
    ) -> Path:
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
        log_file = self.history_dir / f"{timestamp}.json"
        
        # Build deterministic strings for hashing
        plan_str = f"{plan.id}_{plan.estimated_reclaimable_bytes}_{len(plan.actions)}"
        plan_hash = hashlib.sha256(plan_str.encode('utf-8')).hexdigest()
        
        report_str = f"{report.succeeded}_{report.failed}_{report.total_freed_bytes}_{report.duration_ms}"
        report_hash = hashlib.sha256(report_str.encode('utf-8')).hexdigest()
        
        log_data: Dict[str, Any] = {
            "schema_version": "1.0",
            "engine_version": "1.0.0",
            "timestamp": timestamp,
            "plan_id": str(plan.id),
            "mode": mode.value,
            "policy": policy_name,
            "freed_bytes": report.total_freed_bytes,
            "provenance": {
                "devclean_version": "1.0.0",
                "platform": platform.system(),
                "platform_release": platform.release(),
                "python_version": platform.python_version()
            },
            "integrity": {
                "plan_hash": plan_hash,
                "report_hash": report_hash
            },
            "actions": [
                {
                    "action_id": str(a.id),
                    "operation": a.decision.recommendation.operation.value,
                    "target": str(a.decision.item.path),
                    "reason": a.decision.reason.value
                } for a in plan.actions
            ],
            "results": [
                {
                    "action_id": str(r.action_id),
                    "success": r.success,
                    "freed_bytes": r.freed_bytes,
                    "duration_ms": r.duration_ms,
                    "error": r.error
                } for r in report.results
            ]
        }
        
        log_file.write_text(json.dumps(log_data, indent=2), encoding="utf-8")
        return log_file
