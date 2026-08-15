from typing import Iterable
from pathlib import Path
import time
import re

from devclean.domain.services.detector import Detector
from devclean.domain.entities.scan_context import ScanContext
from devclean.domain.entities.audit_item import AuditItem

from devclean.domain.enums.category import Category
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel

from devclean.infrastructure.filesystem.size import calculate_directory_size


class VirtualEnvDetector(Detector):
    @property
    def name(self) -> str:
        return "virtualenvs"

    def detect(self, context: ScanContext) -> Iterable[AuditItem]:
        # Typical venv folder names
        venv_names = {"venv", ".venv", "env", ".env"}
        
        # Scan through all root_paths
        for root in context.root_paths:
            if context.cancelled():
                break
                
            yield from self._scan_directory(root, venv_names, context)

    def _scan_directory(self, path: Path, venv_names: set[str], context: ScanContext) -> Iterable[AuditItem]:
        if not path.exists() or not path.is_dir():
            return
            
        stack = [path]
        
        while stack:
            if context.cancelled():
                break
                
            current = stack.pop()
            try:
                for item in current.iterdir():
                    if context.cancelled():
                        break
                        
                    if item.is_dir() and not item.is_symlink():
                        # Check if this is a venv
                        if item.name in venv_names and (item / "pyvenv.cfg").exists():
                            yield self._analyze_venv(item, context)
                        else:
                            # Avoid diving into node_modules or large hidden folders to save time
                            if item.name not in {"node_modules", ".git"}:
                                stack.append(item)
            except (PermissionError, FileNotFoundError):
                continue

    def _analyze_venv(self, venv_path: Path, context: ScanContext) -> AuditItem:
        size = calculate_directory_size(venv_path, context.cancelled)
        
        # Heuristic 1: Check if pyvenv.cfg points to a valid base interpreter
        cfg_path = venv_path / "pyvenv.cfg"
        base_executable_missing = False
        if cfg_path.exists():
            try:
                content = cfg_path.read_text(encoding="utf-8")
                # Look for executable or home
                match = re.search(r"executable\s*=\s*(.+)", content, re.IGNORECASE)
                if match:
                    base_exe = Path(match.group(1).strip())
                    if not base_exe.exists():
                        base_executable_missing = True
            except Exception:
                pass
                
        # Heuristic 2: Check modification time
        # If older than 180 days
        is_old = False
        try:
            mtime = venv_path.stat().st_mtime
            if (time.time() - mtime) > (180 * 24 * 60 * 60):
                is_old = True
        except Exception:
            pass

        confidence = ConfidenceLevel.HEURISTIC
        explanation = "Python virtual environment."
        safety = "Recreating a virtual environment requires reinstalling all packages from requirements.txt."
        
        if base_executable_missing:
            confidence = ConfidenceLevel.VERIFIED
            explanation = "Appears orphaned because the referenced base interpreter no longer exists."
        elif is_old:
            confidence = ConfidenceLevel.PROBABLE
            explanation = "Virtual environment has not been modified in over 180 days."


        return AuditItem(
            path=venv_path,
            size_bytes=size,
            category=Category.VENV,
            risk_level=RiskLevel.HIGH, # Venvs are always HIGH risk
            description="Python Virtual Environment",
            confidence=confidence,
            is_reclaimable=True
        )
