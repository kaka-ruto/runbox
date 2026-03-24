"""Configuration management for Runbox."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class ServerSettings(BaseSettings):
    """Server configuration."""

    host: str = "0.0.0.0"
    port: int = 8080


class AuthSettings(BaseSettings):
    """Authentication configuration."""

    enabled: bool = True
    api_key: str = Field(default="", alias="RUNBOX_API_KEY")


class ContainerSettings(BaseSettings):
    """Container management configuration."""

    prefix: str = "runbox"
    idle_timeout: int = 3600  # 1 hour in seconds
    work_dir: str = "/app"


class LimitsSettings(BaseSettings):
    """Default resource limits."""

    timeout: int = 30  # seconds
    memory: str = "256m"
    cpu: float = 0.5
    output_max: int = 65536  # bytes


class LanguageConfig(BaseSettings):
    """Configuration for a single language."""

    image: str
    entrypoint_cmd: str


class NetworkSettings(BaseSettings):
    """Network policy configuration."""

    mode: str = "allowlist"  # "allowlist", "denylist", "none"
    default_allowed: list[str] = Field(default_factory=list)


class CleanupSettings(BaseSettings):
    """Cleanup worker configuration."""

    enabled: bool = True
    interval: int = 300  # 5 minutes


class Settings(BaseSettings):
    """Main configuration class."""

    server: ServerSettings = Field(default_factory=ServerSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    containers: ContainerSettings = Field(default_factory=ContainerSettings)
    limits: LimitsSettings = Field(default_factory=LimitsSettings)
    languages: dict[str, LanguageConfig] = Field(default_factory=dict)
    network: NetworkSettings = Field(default_factory=NetworkSettings)
    cleanup: CleanupSettings = Field(default_factory=CleanupSettings)

    model_config = {"env_prefix": "RUNBOX_"}

    @classmethod
    def load(cls, config_path: str | Path | None = None) -> "Settings":
        """Load settings from YAML file and environment variables."""
        config_data: dict[str, Any] = {}

        # Try to load from file
        if config_path:
            path = Path(config_path)
            if path.exists():
                with open(path) as f:
                    config_data = yaml.safe_load(f) or {}
        else:
            # Try default locations
            for default_path in ["runbox.yml", "runbox.yaml", "/etc/runbox/runbox.yml"]:
                path = Path(default_path)
                if path.exists():
                    with open(path) as f:
                        config_data = yaml.safe_load(f) or {}
                    break

        # Set default languages if not configured
        if "languages" not in config_data:
            config_data["languages"] = {
                "python": {
                    "image": "ghcr.io/kaka-ruto/runbox/python:3.11",
                    "entrypoint_cmd": "python",
                },
                "ruby": {
                    "image": "ghcr.io/kaka-ruto/runbox/ruby:3.2",
                    "entrypoint_cmd": "ruby",
                },
                "shell": {
                    "image": "ghcr.io/kaka-ruto/runbox/shell:5.2",
                    "entrypoint_cmd": "bash",
                },
            }

        return cls(**config_data)


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings.load()
    return _settings


def init_settings(config_path: str | Path | None = None) -> Settings:
    """Initialize settings from a specific path."""
    global _settings
    _settings = Settings.load(config_path)
    return _settings
