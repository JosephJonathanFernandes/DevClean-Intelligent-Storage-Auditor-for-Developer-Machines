import time
from typing import Dict, Tuple
from pathlib import Path

from devclean.domain.entities.cleanup_plan import CleanupPlan, CleanupAction
from devclean.domain.entities.cleanup_result import CleanupExecutionReport, ValidationReport, CleanupResult
from devclean.domain.enums.cleanup import CleanupMode, CleanupOperation
from devclean.infrastructure.cleanup.operation_executors import OperationExecutor, DeleteDirectoryExecutor
from devclean.infrastructure.logging.audit_logger import ExecutionHistoryLogger


class AllowedRootPolicy:
    """Enforces path confinement. Rejects operations outside approved root directories."""
    
    def __init__(self, allowed_roots: Tuple[Path, ...]):
        self.allowed_roots = [p.resolve() for p in allowed_roots]
        
    def is_allowed(self, path: Path) -> bool:
        try:
            resolved = path.resolve()
        except Exception:
            return False
            
        for root in self.allowed_roots:
            try:
                # relative_to will raise ValueError if resolved is not under root
                resolved.relative_to(root)
                return True
            except ValueError:
                continue
        return False


class CleanupExecutor:
    """The safe execution engine that manages dry runs, validation, and idempotency."""
    
    def __init__(self, allowed_roots: Tuple[Path, ...], logger: ExecutionHistoryLogger | None = None):
        self.path_policy = AllowedRootPolicy(allowed_roots)
        self.logger = logger or ExecutionHistoryLogger()
        self.executors: Dict[CleanupOperation, OperationExecutor] = {
            CleanupOperation.DELETE_DIRECTORY: DeleteDirectoryExecutor(),
            CleanupOperation.PURGE_CACHE: DeleteDirectoryExecutor(),  # fallback for now
            CleanupOperation.DELETE_FILE: DeleteDirectoryExecutor(),  # fallback for now
        }
        
    def validate(self, plan: CleanupPlan) -> ValidationReport:
        """Pre-execution validation phase."""
        warnings = []
        errors = []
        
        for action in plan.actions:
            if not action.decision:
                errors.append(f"Action {action.id} missing decision")
                continue
                
            for path in action.decision.recommendation.files_affected:
                if not self.path_policy.is_allowed(path):
                    errors.append(f"Security: Path {path} is outside allowed roots!")
                    
                if not path.exists():
                    warnings.append(f"Idempotency: Path {path} already missing.")
                    
        return ValidationReport(
            passed=len(errors) == 0,
            warnings=tuple(warnings),
            errors=tuple(errors)
        )
        
    def execute(self, plan: CleanupPlan, mode: CleanupMode = CleanupMode.DRY_RUN) -> CleanupExecutionReport:
        start_time = time.time()
        
        # 1. Validation
        validation = self.validate(plan)
        if not validation.passed:
            return CleanupExecutionReport(
                succeeded=0, failed=len(plan.actions), skipped=0,
                total_freed_bytes=0, duration_ms=(time.time()-start_time)*1000,
                results=tuple()
            )
            
        if mode in (CleanupMode.DRY_RUN, CleanupMode.VERIFY_ONLY):
            # In dry-run, we assume success for everything validated
            duration_ms = (time.time() - start_time) * 1000
            return CleanupExecutionReport(
                succeeded=len(plan.actions), failed=0, skipped=0,
                total_freed_bytes=plan.estimated_reclaimable_bytes,
                duration_ms=duration_ms,
                results=tuple()
            )
            
        # 2. Execution (checkpoint simulation via loop state)
        succeeded = 0
        failed = 0
        total_freed = 0
        results = []
        
        for action in plan.actions:
            # Checkpoint: In a real system, we might log "Starting action X"
            operation = action.decision.recommendation.operation
            executor = self.executors.get(operation)
            
            if not executor:
                results.append(CleanupResult(
                    action_id=action.id, success=False, freed_bytes=0, duration_ms=0.0,
                    error=f"No executor for {operation}", rollback_available=False
                ))
                failed += 1
                continue
                
            result = executor.execute(action)
            results.append(result)
            
            if result.success:
                succeeded += 1
                total_freed += result.freed_bytes
            else:
                failed += 1
                
        duration_ms = (time.time() - start_time) * 1000
        
        report = CleanupExecutionReport(
            succeeded=succeeded,
            failed=failed,
            skipped=0, # Skipped logic can be added for missing dependencies
            total_freed_bytes=total_freed,
            duration_ms=duration_ms,
            results=tuple(results)
        )
        
        # Log the execution history
        try:
            self.logger.log_execution(plan, report, mode, "execution_policy") # The policy name could be passed down, but for now we log it.
        except Exception:
            pass # We don't fail the execution if logging fails
            
        return report
