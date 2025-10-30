from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional
import json


@dataclass(slots=True)
class ContainerConfig:
    """Konfiguracja pojedynczego kontenera."""

    name: str
    base_url: str
    timeout: float = 10.0
    retries: int = 3
    extra_headers: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True

    @staticmethod
    def from_mapping(name: str, data: Mapping[str, Any]) -> "ContainerConfig":
        return ContainerConfig(
            name=name,
            base_url=str(data.get("base_url", "")),
            timeout=float(data.get("timeout", 10.0)),
            retries=int(data.get("retries", 3)),
            extra_headers=dict(data.get("extra_headers", {})),
            enabled=bool(data.get("enabled", True)),
        )


@dataclass(slots=True)
class AgentConfig:
    """Konfiguracja główna agenta."""

    meta_goal: str
    containers: Dict[str, ContainerConfig]
    log_path: Optional[Path] = None
    dry_run: bool = False

    @staticmethod
    def from_dict(data: Mapping[str, Any]) -> "AgentConfig":
        containers = {
            name: ContainerConfig.from_mapping(name, cfg)
            for name, cfg in data.get("containers", {}).items()
        }
        log_path = data.get("log_path")
        return AgentConfig(
            meta_goal=str(data.get("meta_goal", "utrzymuj reaktywnego asystenta")),
            containers=containers,
            log_path=Path(log_path) if log_path else None,
            dry_run=bool(data.get("dry_run", False)),
        )

    @staticmethod
    def load(path: str | Path) -> "AgentConfig":
        """Wczytuje konfigurację z pliku JSON."""

        config_path = Path(path)
        with config_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return AgentConfig.from_dict(data)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "meta_goal": self.meta_goal,
            "log_path": str(self.log_path) if self.log_path else None,
            "dry_run": self.dry_run,
            "containers": {
                name: {
                    "name": cfg.name,
                    "base_url": cfg.base_url,
                    "timeout": cfg.timeout,
                    "retries": cfg.retries,
                    "extra_headers": cfg.extra_headers,
                    "enabled": cfg.enabled,
                }
                for name, cfg in self.containers.items()
            },
        }
