from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from agent import AgentConfig, AgentLoop


DEFAULT_CONFIG_PATH = Path("config/agent.config.json")


def load_or_create_config(path: Path) -> AgentConfig:
    if path.exists():
        return AgentConfig.load(path)

    # Konfiguracja przykładowa (dry-run)
    default = {
        "meta_goal": "utrzymuj reaktywnego asystenta obsługującego kontenery",
        "dry_run": True,
        "containers": {
            "tts": {
                "base_url": "http://localhost:8081/tasks",
                "timeout": 10,
                "retries": 2,
            },
            "stt": {
                "base_url": "http://localhost:8082/tasks",
                "timeout": 15,
                "retries": 2,
            },
            "aux": {
                "base_url": "http://localhost:8090/tasks",
                "timeout": 20,
                "retries": 3,
            },
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(default, handle, indent=2, ensure_ascii=False)
    print(f"[Agent] Utworzono domyślną konfigurację w {path} (tryb dry-run).", file=sys.stderr)
    return AgentConfig.from_dict(default)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reaktywny agent do obsługi kontenerów TTS/STT")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Ścieżka do pliku konfiguracji JSON",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path: Path = args.config

    try:
        config = load_or_create_config(config_path)
    except Exception as exc:  # pragma: no cover - zależne od środowiska
        print(f"[Agent] Błąd wczytywania konfiguracji: {exc}", file=sys.stderr)
        return 1

    loop = AgentLoop(config)
    loop.run()
    return 0


if __name__ == "__main__":  # pragma: no cover - uruchamiane interaktywnie
    raise SystemExit(main())
