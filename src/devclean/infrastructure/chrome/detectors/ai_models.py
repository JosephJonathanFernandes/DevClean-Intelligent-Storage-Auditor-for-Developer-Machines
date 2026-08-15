from typing import Iterable
from pathlib import Path
import re

from devclean.domain.services.detector import Detector
from devclean.domain.entities.scan_context import ScanContext
from devclean.domain.entities.audit_item import AuditItem

from devclean.domain.enums.category import Category
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel
from devclean.domain.enums.cleanup import RollbackStrategy, CleanupOperation
from devclean.infrastructure.filesystem.size import calculate_directory_size


class ChromeAIModelDetector(Detector):
    @property
    def name(self) -> str:
        return "chrome_ai_models"

    def detect(self, context: ScanContext) -> Iterable[AuditItem]:
        chrome_user_data = context.services.paths.local_app_data / "Google" / "Chrome" / "User Data"
        
        if not chrome_user_data.exists():
            return
            
        # Patterns recommended by user
        patterns = [
            r"OptGuideOnDeviceModel",
            r"OptimizationGuidePredict.*",
            r"OptimizationGuideModelStore",
            r"OnDevice.*Model"
        ]
        
        try:
            for item in chrome_user_data.iterdir():
                if context.cancelled():
                    break
                    
                if not item.is_dir():
                    continue
                    
                for pattern in patterns:
                    if re.match(pattern, item.name, re.IGNORECASE):
                        size = calculate_directory_size(item, context.cancelled)
                        

                        yield AuditItem(
                            path=item,
                            size_bytes=size,
                            category=Category.CHROME_AI_MODEL,
                            risk_level=RiskLevel.LOW,
                            description=f"Chrome AI Model Storage ({item.name})",
                            confidence=ConfidenceLevel.VERIFIED,
                            is_reclaimable=True
                        )
                        break # Prevent yielding same folder twice if it matches multiple patterns
        except (PermissionError, FileNotFoundError):
            pass
