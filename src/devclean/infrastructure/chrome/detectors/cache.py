from typing import Iterable
from pathlib import Path

from devclean.domain.services.detector import Detector
from devclean.domain.entities.scan_context import ScanContext
from devclean.domain.entities.audit_item import AuditItem

from devclean.domain.enums.category import Category
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel
from devclean.domain.enums.cleanup import RollbackStrategy, CleanupOperation
from devclean.infrastructure.filesystem.size import calculate_directory_size


class ChromeCacheDetector(Detector):
    @property
    def name(self) -> str:
        return "chrome_cache"

    def detect(self, context: ScanContext) -> Iterable[AuditItem]:
        chrome_user_data = context.services.paths.local_app_data / "Google" / "Chrome" / "User Data"
        
        if not chrome_user_data.exists():
            return
            
        cache_names = {"Cache", "Code Cache", "GPUCache"}
        
        try:
            for profile in chrome_user_data.iterdir():
                if context.cancelled():
                    break
                    
                if not profile.is_dir():
                    continue
                    
                # Cache can be in Default/Cache, Default/Code Cache, etc.
                for cache_dir_name in cache_names:
                    cache_dir = profile / cache_dir_name
                    
                    if cache_dir.exists() and cache_dir.is_dir():
                        size = calculate_directory_size(cache_dir, context.cancelled)
                        

                        yield AuditItem(
                            path=cache_dir,
                            size_bytes=size,
                            category=Category.BROWSER_CACHE,
                            risk_level=RiskLevel.SAFE,
                            description=f"Chrome {cache_dir_name} ({profile.name})",
                            confidence=ConfidenceLevel.VERIFIED,
                            is_reclaimable=True
                        )
        except (PermissionError, FileNotFoundError):
            pass
