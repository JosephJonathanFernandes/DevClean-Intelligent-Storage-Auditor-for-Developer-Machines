from devclean.domain.services.analyzer import Analyzer

class RegistryFrozenError(Exception):
    """Raised when attempting to modify a frozen registry."""
    pass

class AnalyzerRegistry:
    def __init__(self) -> None:
        self._analyzers: dict[str, Analyzer] = {}
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
