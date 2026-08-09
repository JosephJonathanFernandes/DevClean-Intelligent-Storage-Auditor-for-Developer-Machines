from typing import Iterable
from pathlib import Path

from devclean.domain.entities.scan_context import ScanContext
from devclean.domain.services.wsl_provider import WSLProvider, WSLDistroInfo

class FilesystemWSLProvider(WSLProvider):
    def __init__(self, context: ScanContext):
        self.context = context

    def get_distros(self) -> Iterable[WSLDistroInfo]:
        """
        Inspects %LOCALAPPDATA%\Packages for WSL distro virtual disks.
        """
        packages_dir = self.context.services.paths.local_app_data / "Packages"
        if not self.context.services.fs.is_dir(packages_dir):
            return

        # CanonicalGroupLimited.Ubuntu, TheDebianProject, etc.
        # We look for LocalState/ext4.vhdx in all package folders.
        try:
            for package_folder in packages_dir.iterdir():
                if not self.context.services.fs.is_dir(package_folder):
                    continue
                    
                vhdx_path = package_folder / "LocalState" / "ext4.vhdx"
                if self.context.services.fs.is_file(vhdx_path):
                    # Heuristic name extraction
                    distro_name = package_folder.name.split("_")[0]
                    
                    yield WSLDistroInfo(
                        name=distro_name,
                        disk_path=vhdx_path,
                        size_bytes=self.context.services.fs.size(vhdx_path),
                        last_modified=self.context.services.fs.modified_time(vhdx_path)
                    )
        except Exception:
            pass
