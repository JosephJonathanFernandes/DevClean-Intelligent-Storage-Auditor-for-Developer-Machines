from typing import Iterable
from pathlib import Path
import uuid

from devclean.domain.services.detector import Detector
from devclean.domain.entities.scan_context import ScanContext
from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.entities.recommendation import Recommendation
from devclean.domain.enums.category import Category
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel
from devclean.domain.enums.rollback_difficulty import RollbackDifficulty
from devclean.infrastructure.filesystem.size import calculate_directory_size


class PipCacheDetector(Detector):
    @property
    def name(self) -> str:
        return "pip_cache"

    def detect(self, context: ScanContext) -> Iterable[AuditItem]:
        local_app_data = context.services.paths.local_app_data
        
        # Standard pip cache on Windows: %LOCALAPPDATA%\pip\cache
        # Or Unix: ~/.cache/pip
        pip_cache_path = local_app_data / "pip" / "cache"
        
        if pip_cache_path.exists() and pip_cache_path.is_dir():
            if context.cancelled():
                return
                
            size = calculate_directory_size(pip_cache_path, context.cancelled)
            
            if size > 0:
                rec = Recommendation(
                    title="Purge pip download cache",
                    explanation="This cache stores downloaded package archives. Deleting it will not uninstall installed Python packages.",
                    safety_reason="Contains downloaded package archives only. Installed packages are not affected.",
                    rollback=RollbackDifficulty.AUTOMATIC,
                    rollback_notes="Cache will regenerate automatically when downloading new packages.",
                    command="py -m pip cache purge" if context.platform.value == "windows" else "python -m pip cache purge",
                    files_affected=(pip_cache_path,)
                )
                
                yield AuditItem(
                    path=pip_cache_path,
                    size_bytes=size,
                    category=Category.PYTHON_CACHE,
                    risk_level=RiskLevel.SAFE,
                    description="Pip package download cache",
                    confidence=ConfidenceLevel.VERIFIED,
                    recommendation=rec,
                    is_reclaimable=True
                )
