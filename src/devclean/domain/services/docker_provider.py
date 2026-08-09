from typing import Protocol, Iterable
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

@dataclass(frozen=True)
class DockerVolumeInfo:
    name: str
    path: Path
    size_bytes: int
    last_modified: datetime

class DockerProvider(Protocol):
    """
    Abstracts the retrieval of Docker state.
    Implementations may use pure filesystem heuristics or subprocesses (e.g. docker system df).
    """
    def get_wsl_backend_disk(self) -> Path | None: ...
    def get_volumes(self) -> Iterable[DockerVolumeInfo]: ...
    def get_build_cache_dirs(self) -> Iterable[Path]: ...
