import logging
import importlib.metadata
from typing import Dict, List, Type

from devclean.domain.services.analyzer import Analyzer

logger = logging.getLogger(__name__)

class RegistryFrozenError(Exception):
    """Raised when attempting to modify a frozen registry."""
    pass

class AnalyzerRegistry:
    def __init__(self) -> None:
        self._analyzers: dict[str, Analyzer] = {}
        self._failed_plugins: dict[str, str] = {}
        self._frozen: bool = False

    def register(self, analyzer: Analyzer) -> None:
        if self._frozen:
            raise RegistryFrozenError("Cannot register analyzers after registry is frozen.")
        self._analyzers[analyzer.metadata.name] = analyzer

    def freeze(self) -> None:
        """Lock the registry to prevent runtime mutation bugs."""
        self._frozen = True

    def get_all(self) -> list[Analyzer]:
        # Return sorted by priority (lowest number = highest priority)
        return sorted(self._analyzers.values(), key=lambda a: a.metadata.priority)
        
    def get_failed_plugins(self) -> dict[str, str]:
        """Returns a dict of plugin name to error message."""
        return self._failed_plugins.copy()

    def load_plugins(self) -> None:
        """Discover and load external analyzers via entry points."""
        if self._frozen:
            raise RegistryFrozenError("Cannot load plugins after registry is frozen.")
            
        group = "devclean.analyzers"
        try:
            # Python 3.10+
            eps = importlib.metadata.entry_points(group=group)
        except TypeError:
            # Fallback for < 3.10 if needed
            eps = importlib.metadata.entry_points().get(group, [])

        for ep in eps:
            try:
                analyzer_cls: Type[Analyzer] = ep.load()
                # Instantiate
                analyzer_instance = analyzer_cls()
                self.register(analyzer_instance)
                logger.debug(f"Loaded plugin: {ep.name}")
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                self._failed_plugins[ep.name] = error_msg
                logger.warning(f"Failed to load plugin '{ep.name}': {error_msg}")
