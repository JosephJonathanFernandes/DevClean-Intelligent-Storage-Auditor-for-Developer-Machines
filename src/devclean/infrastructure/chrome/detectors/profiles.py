from typing import Iterable
from pathlib import Path
import re

from devclean.domain.services.detector import Detector
from devclean.domain.entities.scan_context import ScanContext
from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.entities.recommendation import Recommendation
from devclean.domain.enums.category import Category
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel
from devclean.domain.enums.rollback_difficulty import RollbackDifficulty
from devclean.infrastructure.filesystem.size import calculate_directory_size


class ChromeProfileDetector(Detector):
    @property
    def name(self) -> str:
        return "chrome_profiles"

    def detect(self, context: ScanContext) -> Iterable[AuditItem]:
        chrome_user_data = context.services.paths.local_app_data / "Google" / "Chrome" / "User Data"
        
        if not chrome_user_data.exists():
            return
            
        try:
            for item in chrome_user_data.iterdir():
                if context.cancelled():
                    break
                    
                if not item.is_dir():
                    continue
                    
                # Match "Default" or "Profile X"
                if item.name == "Default" or re.match(r"^Profile \d+$", item.name):
                    size = calculate_directory_size(item, context.cancelled)
                    
                    rec = Recommendation(
                        title="Delete Chrome Profile",
                        explanation=f"User profile directory: {item.name}.",
                        safety_reason="Deleting this will remove all browsing history, bookmarks, passwords, and extensions for this profile.",
                        rollback=RollbackDifficulty.IMPOSSIBLE,
                        rollback_notes="Data cannot be recovered unless it was synced to a Google account.",
                        files_affected=(item,)
                    )
                    
                    yield AuditItem(
                        path=item,
                        size_bytes=size,
                        category=Category.CHROME_PROFILE,
                        risk_level=RiskLevel.HIGH,
                        description=f"Chrome Profile: {item.name}",
                        confidence=ConfidenceLevel.VERIFIED,
                        recommendation=rec,
                        is_reclaimable=False # By default, don't recommend deleting profiles
                    )
        except (PermissionError, FileNotFoundError):
            pass
