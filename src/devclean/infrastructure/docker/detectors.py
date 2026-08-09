from typing import Iterable
from devclean.domain.entities.scan_context import ScanContext
from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.entities.recommendation import Recommendation
from devclean.domain.enums.category import Category
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel
from devclean.domain.enums.rollback_difficulty import RollbackDifficulty
from devclean.domain.services.detector import Detector
from devclean.infrastructure.docker.filesystem_provider import FilesystemDockerProvider

class DockerBackendDetector(Detector):
    @property
    def name(self) -> str:
        return "docker_backend"

    def detect(self, context: ScanContext) -> Iterable[AuditItem]:
        provider = FilesystemDockerProvider(context)
        disk_path = provider.get_wsl_backend_disk()
        
        if disk_path:
            yield AuditItem(
                path=disk_path,
                size_bytes=context.services.fs.size(disk_path),
                category=Category.SYSTEM_CACHE, # It's a system cache for docker
                risk_level=RiskLevel.HIGH, # Deleting it destroys everything
                description="Docker Desktop WSL virtual disk",
                confidence=ConfidenceLevel.VERIFIED,
                is_reclaimable=False, # We don't recommend auto-deletion
                last_modified=context.services.fs.modified_time(disk_path),
                metadata={
                    "type": "wsl_vhdx",
                    "provider": "docker_desktop"
                },
                recommendation=Recommendation(
                    title="Review Docker WSL backend storage",
                    explanation="Docker Desktop stores images and volumes inside a WSL virtual disk.",
                    rollback=RollbackDifficulty.MANUAL,
                    safety_reason="Deleting the virtual disk can destroy all Docker images and volumes."
                )
            )

class DockerVolumeDetector(Detector):
    @property
    def name(self) -> str:
        return "docker_volumes"

    def detect(self, context: ScanContext) -> Iterable[AuditItem]:
        provider = FilesystemDockerProvider(context)
        for vol in provider.get_volumes():
            yield AuditItem(
                path=vol.path,
                size_bytes=vol.size_bytes,
                category=Category.PROJECT_DEPENDENCY,
                risk_level=RiskLevel.MODERATE,
                description=f"Docker Volume: {vol.name}",
                confidence=ConfidenceLevel.PROBABLE,
                is_reclaimable=True,
                last_modified=vol.last_modified,
                metadata={
                    "volume_name": vol.name
                },
                recommendation=Recommendation(
                    title=f"Review Docker Volume: {vol.name}",
                    explanation="This is a Docker volume. It may contain database files or persistent state.",
                    rollback=RollbackDifficulty.MANUAL,
                    safety_reason="If this volume contains a database, deleting it will result in permanent data loss.",
                    command=f"docker volume rm {vol.name}"
                )
            )

class DockerBuildCacheDetector(Detector):
    @property
    def name(self) -> str:
        return "docker_build_cache"

    def detect(self, context: ScanContext) -> Iterable[AuditItem]:
        provider = FilesystemDockerProvider(context)
        for cache_dir in provider.get_build_cache_dirs():
            yield AuditItem(
                path=cache_dir,
                size_bytes=context.services.fs.size(cache_dir),
                category=Category.BUILD_ARTIFACT,
                risk_level=RiskLevel.SAFE,
                description="Docker BuildKit Cache",
                confidence=ConfidenceLevel.VERIFIED,
                is_reclaimable=True,
                last_modified=context.services.fs.modified_time(cache_dir),
                metadata={
                    "cache_type": "buildkit"
                },
                recommendation=Recommendation(
                    title="Clear Docker BuildKit Cache",
                    explanation="Docker caches build layers here. They can be safely deleted to reclaim space.",
                    rollback=RollbackDifficulty.EASY,
                    safety_reason="Build caches will automatically regenerate on the next docker build.",
                    command="docker builder prune -a -f"
                )
            )
