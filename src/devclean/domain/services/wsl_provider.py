from typing import Protocol, Iterable
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

@dataclass(frozen=True)
class WSLDistroInfo:
    name: str
    disk_path: Path
    size_bytes: int
    last_modified: datetime

class WSLProvider(Protocol):
    """
    Abstracts the retrieval of Windows Subsystem for Linux (WSL) state.
    Implementations may use pure filesystem heuristics or subprocesses (e.g. wsl.exe -l -v).
    """
    def get_distros(self) -> Iterable[WSLDistroInfo]: ...
