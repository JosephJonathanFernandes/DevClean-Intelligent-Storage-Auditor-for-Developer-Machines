from typing import Iterable
from pathlib import Path
import uuid

from devclean.domain.services.detector import Detector
from devclean.domain.entities.scan_context import ScanContext
from devclean.domain.entities.audit_item import AuditItem

from devclean.domain.enums.category import Category
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel

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

                yield AuditItem(
                    path=pip_cache_path,
                    size_bytes=size,
                    category=Category.PYTHON_CACHE,
                    risk_level=RiskLevel.SAFE,
                    description="Pip package download cache",
                    confidence=ConfidenceLevel.VERIFIED,
                    is_reclaimable=True
                )
