import shutil
import time
from typing import Protocol
from devclean.domain.entities.cleanup_plan import CleanupAction
from devclean.domain.entities.cleanup_result import CleanupResult
from devclean.domain.enums.cleanup import RollbackStrategy

class OperationExecutor(Protocol):
    def execute(self, action: CleanupAction) -> CleanupResult:
        """Executes a specific cleanup action and returns the result."""
        ...

class DeleteDirectoryExecutor:
    def execute(self, action: CleanupAction) -> CleanupResult:
        start_time = time.time()
        freed_bytes = 0
        success = True
        error_msg = None
        
        try:
            for path in action.decision.recommendation.files_affected:
                if not path.exists():
                    # Idempotency: missing directory -> success
                    continue
                    
                if not path.is_dir():
                    success = False
                    error_msg = f"Path {path} is not a directory"
                    break
                    
                # Note: this is a naive recursive delete. In a real scenario we'd calculate freed_bytes accurately.
                freed_bytes += action.decision.item.size_bytes # Approximate
                shutil.rmtree(path)
                
        except PermissionError as e:
            success = False
            error_msg = f"Permission denied: {e}"
        except OSError as e:
            success = False
            error_msg = f"OS error: {e}"
            
        duration_ms = (time.time() - start_time) * 1000
        
        return CleanupResult(
            action_id=action.id,
            success=success,
            freed_bytes=freed_bytes if success else 0,
            duration_ms=duration_ms,
            error=error_msg,
            rollback_available=action.decision.recommendation.rollback != RollbackStrategy.NO_ROLLBACK_AVAILABLE
        )

# Future: DeleteFileExecutor, PurgeCacheExecutor, etc.
