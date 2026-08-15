import json
from uuid import UUID
from pathlib import Path
from enum import Enum
from dataclasses import is_dataclass, asdict

class DevCleanJSONEncoder(json.JSONEncoder):
    """Encodes DevClean domain entities to JSON securely."""
    def default(self, obj):
        if is_dataclass(obj):
            return asdict(obj)
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)
