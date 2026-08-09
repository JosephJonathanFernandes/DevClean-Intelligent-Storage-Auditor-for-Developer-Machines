from typing import Iterable
from pathlib import Path

from devclean.domain.entities.scan_context import ScanContext
from devclean.domain.services.docker_provider import DockerProvider, DockerVolumeInfo

class FilesystemDockerProvider(DockerProvider):
    def __init__(self, context: ScanContext):
        self.context = context

    def get_wsl_backend_disk(self) -> Path | None:
        """Finds the main ext4.vhdx for Docker Desktop WSL."""
        disk_path = self.context.services.paths.local_app_data / "Docker" / "wsl" / "data" / "ext4.vhdx"
        if self.context.services.fs.is_file(disk_path):
            return disk_path
        return None

    def get_volumes(self) -> Iterable[DockerVolumeInfo]:
        """
        Attempts to find volumes via the WSL 9P network share.
        Note: This only works if Docker Desktop is currently running.
        """
        # We can't guarantee \\wsl$ is mounted, but if it is:
        volumes_path = Path(r"\\wsl$\docker-desktop-data\version-pack-data\community\docker\volumes")
        try:
            if self.context.services.fs.is_dir(volumes_path):
                # Iterate through volume directories
                for item in volumes_path.iterdir():
                    if self.context.services.fs.is_dir(item) and item.name != "metadata.db":
                        yield DockerVolumeInfo(
                            name=item.name,
                            path=item,
                            size_bytes=self._get_dir_size(item),
                            last_modified=self.context.services.fs.modified_time(item)
                        )
        except OSError:
            pass
                    
    def get_build_cache_dirs(self) -> Iterable[Path]:
        """Attempts to find buildx/buildkit cache dirs."""
        buildkit_path = Path(r"\\wsl$\docker-desktop-data\version-pack-data\community\docker\buildkit")
        try:
            if self.context.services.fs.is_dir(buildkit_path):
                yield buildkit_path
        except OSError:
            pass

    def _get_dir_size(self, path: Path) -> int:
        total = 0
        try:
            for item in path.rglob("*"):
                if self.context.services.fs.is_file(item):
                    total += self.context.services.fs.size(item)
        except Exception:
            pass # Ignore permissions or network drop errors
        return total
