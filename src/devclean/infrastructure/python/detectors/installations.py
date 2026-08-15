from typing import Iterable
from pathlib import Path
import re

from devclean.domain.services.detector import Detector
from devclean.domain.entities.scan_context import ScanContext
from devclean.domain.entities.audit_item import AuditItem

from devclean.domain.enums.category import Category
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel

from devclean.infrastructure.filesystem.size import calculate_directory_size


class InstallationDetector(Detector):
    @property
    def name(self) -> str:
        return "python_installations"

    def detect(self, context: ScanContext) -> Iterable[AuditItem]:
        # Track versions to find duplicates
        installations: dict[str, list[Path]] = {}
        
        candidates = [
            context.services.paths.local_app_data / "Programs" / "Python",
            context.services.paths.windows_apps,
            context.services.paths.program_files / "Python",
            context.services.paths.program_files_x86 / "Python" if context.services.paths.program_files_x86 else None,
            context.services.paths.user_profile / ".pyenv" / "pyenv-win" / "versions",
            context.services.paths.user_profile / ".rye" / "py",
        ]
        
        for base_path in candidates:
            if not base_path or not base_path.exists() or context.cancelled():
                continue
                
            try:
                for item in base_path.iterdir():
                    if not item.is_dir():
                        continue
                        
                    # Basic check if it's a python installation
                    if (item / "python.exe").exists() or (item / "python").exists():
                        version = self._guess_version(item)
                        if version not in installations:
                            installations[version] = []
                        installations[version].append(item)
            except (PermissionError, FileNotFoundError):
                continue
                
        # Yield all installations and flag duplicates
        for version, paths in installations.items():
            if context.cancelled():
                break
                
            # Sort paths to keep standard locations as the "primary" and others as duplicates
            # A simple heuristic: shortest path is primary
            sorted_paths = sorted(paths, key=lambda p: len(str(p)))
            primary = sorted_paths[0]
            
            for path in sorted_paths:
                is_duplicate = path != primary
                size = calculate_directory_size(path, context.cancelled)
                
                explanation = f"Python {version} installation."
                title = "Uninstall Python"
                confidence = ConfidenceLevel.VERIFIED
                
                if is_duplicate:
                    explanation = f"Potential duplicate of Python {version} located at {primary}."
                    title = "Remove duplicate Python installation"
                    confidence = ConfidenceLevel.PROBABLE
                    

                yield AuditItem(
                    path=path,
                    size_bytes=size,
                    category=Category.UNKNOWN,  # User didn't specify Python Install category, UNKNOWN or create one? Let's use UNKNOWN
                    risk_level=RiskLevel.HIGH,
                    description=f"Python {version} Installation",
                    confidence=confidence,
                    is_reclaimable=is_duplicate, # Only mark duplicates as reclaimable by default
                    metadata={"version": version, "is_duplicate": is_duplicate, "primary_path": str(primary) if is_duplicate else None}
                )

    def _guess_version(self, path: Path) -> str:
        # Very simple heuristic: look at the folder name
        name = path.name.lower()
        # e.g. Python311 -> 3.11
        match = re.search(r'python(\d)(\d+)', name)
        if match:
            return f"{match.group(1)}.{match.group(2)}"
        
        # e.g. 3.11.2
        match = re.search(r'(\d+\.\d+\.\d+)', name)
        if match:
            return match.group(1)
            
        return "Unknown Version"
