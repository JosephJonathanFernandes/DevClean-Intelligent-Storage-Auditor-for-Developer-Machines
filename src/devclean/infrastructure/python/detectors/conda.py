from typing import Iterable
from pathlib import Path

from devclean.domain.services.detector import Detector
from devclean.domain.entities.scan_context import ScanContext
from devclean.domain.entities.audit_item import AuditItem

from devclean.domain.enums.category import Category
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel

from devclean.infrastructure.filesystem.size import calculate_directory_size


class CondaDetector(Detector):
    @property
    def name(self) -> str:
        return "conda_envs"

    def detect(self, context: ScanContext) -> Iterable[AuditItem]:
        candidates = [
            context.services.paths.user_profile / "miniconda3" / "envs",
            context.services.paths.user_profile / "anaconda3" / "envs",
            context.services.paths.local_app_data / "conda" / "conda" / "envs"
        ]
        
        for base_path in candidates:
            if not base_path.exists() or context.cancelled():
                continue
                
            try:
                for env_dir in base_path.iterdir():
                    if context.cancelled():
                        break
                        
                    if not env_dir.is_dir():
                        continue
                        
                    size = calculate_directory_size(env_dir, context.cancelled)
                    

                    yield AuditItem(
                        path=env_dir,
                        size_bytes=size,
                        category=Category.CONDA_ENV,
                        risk_level=RiskLevel.HIGH,
                        description=f"Conda Environment: {env_dir.name}",
                        confidence=ConfidenceLevel.VERIFIED,
                        is_reclaimable=True
                    )
            except (PermissionError, FileNotFoundError):
                continue
