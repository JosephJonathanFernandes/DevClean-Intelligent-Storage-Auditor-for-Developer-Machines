import os
from pathlib import Path
from dataclasses import dataclass, field
import tomllib

@dataclass
class ScanSettings:
    exclude: list[str] = field(default_factory=list)

@dataclass
class CleanupSettings:
    policy: str = "balanced"

@dataclass
class ReportSettings:
    default_format: str = "html"

@dataclass
class Settings:
    scan: ScanSettings = field(default_factory=ScanSettings)
    cleanup: CleanupSettings = field(default_factory=CleanupSettings)
    reports: ReportSettings = field(default_factory=ReportSettings)
    config_path: Path | None = None

    @classmethod
    def load(cls, config_file: Path | None = None) -> "Settings":
        """
        Layered configuration parsing:
        1. Built-in defaults (via dataclass fields)
        2. `~/.devclean/config.toml` (if exists, or custom `config_file`)
        3. Environment variables
        """
        settings = cls()
        
        # Determine config path
        if config_file is None:
            default_config = Path.home() / ".devclean" / "config.toml"
            if default_config.exists():
                settings.config_path = default_config
        else:
            settings.config_path = config_file

        # Load from TOML
        if settings.config_path and settings.config_path.exists():
            try:
                with settings.config_path.open("rb") as f:
                    data = tomllib.load(f)
                    
                if "scan" in data:
                    settings.scan.exclude = data["scan"].get("exclude", settings.scan.exclude)
                if "cleanup" in data:
                    settings.cleanup.policy = data["cleanup"].get("policy", settings.cleanup.policy)
                if "reports" in data:
                    settings.reports.default_format = data["reports"].get("default_format", settings.reports.default_format)
            except Exception as e:
                # In a real app we'd log this, but we'll let it fail soft for now
                pass

        # Load from Environment Variables
        env_exclude = os.getenv("DEVCLEAN_EXCLUDE")
        if env_exclude is not None:
            # e.g. "node_modules,.git"
            settings.scan.exclude = [x.strip() for x in env_exclude.split(",") if x.strip()]
            
        env_policy = os.getenv("DEVCLEAN_POLICY")
        if env_policy:
            settings.cleanup.policy = env_policy
            
        return settings
