# DevClean Plugin Developer Guide

DevClean features a deeply decoupled Clean Architecture that separates **Discovery** (finding facts on the disk) from **Prescription** (deciding what to do with those facts).

This means writing a plugin is incredibly straightforward: your only job is to discover facts.

## 1. The Analyzer Interface

To build a plugin, you must implement the `Analyzer` interface from `devclean.domain.services.analyzer`. 
An Analyzer is responsible for returning a list of `AuditItem`s. It never returns recommendations.

```python
from pathlib import Path
from typing import List, Callable
from devclean.domain.services.analyzer import Analyzer
from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.enums.category import AuditCategory

class MyCustomAnalyzer(Analyzer):
    @property
    def name(self) -> str:
        return "my-custom-analyzer"
        
    def analyze(self, root_paths: List[Path], is_cancelled: Callable[[], bool]) -> List[AuditItem]:
        items = []
        for path in root_paths:
            if is_cancelled():
                break
                
            # Your detection logic here...
            if path.name == "my_temp_cache":
                items.append(AuditItem(
                    path=path,
                    size_bytes=self._calculate_size(path),
                    category=AuditCategory.OTHER,
                    last_accessed_days=10
                ))
        return items
```

## 2. Recommendation Integration

Once your plugin discovers an `AuditItem`, the core DevClean `RecommendationEngine` evaluates it using its configured rules.

If your plugin identifies artifacts that don't fit into existing categories (like `node-modules` or `python-cache`), you can configure the engine's `RecommendationRules` in `devclean.application.cleanup.recommendation_rules` or inject custom rules via `config.toml`. The engine will evaluate the size, last access time, and platform context to recommend a cleanup action (Delete, Compress, Keep).

## 3. Registration (Entry Points)

DevClean dynamically discovers plugins via Python's standard `entry_points` mechanism.
To register your analyzer so DevClean automatically finds and runs it, add the following to your package's `pyproject.toml` or `setup.py`:

**pyproject.toml**
```toml
[project.entry-points."devclean.analyzers"]
my_custom_plugin = "my_package.module:MyCustomAnalyzer"
```

When users `pip install` your package alongside DevClean, DevClean will securely load and execute your analyzer inside the `AnalyzerRegistry`.

## 4. Testing & Safety

- **No side effects:** Your `analyze` method must be strictly read-only. Do not mutate the filesystem during discovery.
- **Cancellation handling:** Always check the `is_cancelled()` callback during long directory traversals so the user can abort safely.
- **Isolation:** If your plugin raises an exception, the DevClean engine will gracefully catch it, suppress it, and log the failure. It will not crash the user's scan. You can check `devclean doctor` to see if your plugin was successfully loaded or failed.
