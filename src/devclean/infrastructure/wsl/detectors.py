from typing import Iterable
from devclean.domain.entities.scan_context import ScanContext
from devclean.domain.entities.audit_item import AuditItem

from devclean.domain.enums.category import Category
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel

from devclean.domain.services.detector import Detector
from devclean.infrastructure.wsl.filesystem_provider import FilesystemWSLProvider

class WSLDistroDetector(Detector):
    @property
    def name(self) -> str:
        return "wsl_distros"

    def detect(self, context: ScanContext) -> Iterable[AuditItem]:
        provider = FilesystemWSLProvider(context)
        for distro in provider.get_distros():
            yield AuditItem(
                path=distro.disk_path,
                size_bytes=distro.size_bytes,
                category=Category.SYSTEM_CACHE,
                risk_level=RiskLevel.HIGH,
                description=f"WSL Distribution Disk: {distro.name}",
                confidence=ConfidenceLevel.VERIFIED,
                is_reclaimable=False, # We never auto-delete WSL VMs
                last_modified=distro.last_modified,
                metadata={
                    "distribution": distro.name,
                    "disk_type": "ext4.vhdx"
                },

            )
