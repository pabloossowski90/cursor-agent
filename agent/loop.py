from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional, Tuple
import logging
import json

from .config import AgentConfig
from .context import AgentState
from .containers import ContainerManager
from .router import CommandRouter
from .tasks import AgentResponse, TaskResult, UserCommand, ISO8601


logger = logging.getLogger(__name__)


class AgentLoop:
    """Pętla główna reagującego agenta."""

    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.state = AgentState(meta_goal=config.meta_goal)
        self.router = CommandRouter(default_context={"agent": "reactive-vps"})
        self.containers = ContainerManager(config)

    def process(self, command_text: str, metadata: Optional[Dict] = None) -> AgentResponse:
        metadata = metadata.copy() if metadata else {}
        timestamp = self._resolve_timestamp(metadata)
        user_command = UserCommand(text=command_text, timestamp=timestamp, metadata=metadata)
        self.state.record_command(user_command)

        routed = self.router.route(user_command)
        results = self.containers.dispatch_many(routed.tasks)
        self.state.record_results(results)

        if self.config.log_path:
            try:
                self.state.dump_history(self.config.log_path)
            except Exception as exc:  # pragma: no cover - zależne od środowiska
                logger.warning("Nie udało się zapisać historii: %s", exc)

        message = self._build_message(results, routed.notes)
        snapshot = self.state.to_snapshot()
        return AgentResponse(message=message, tasks=routed.tasks, results=results, state_snapshot=snapshot)

    def run(self) -> None:
        self._configure_logging()
        print("[Agent] Witaj! Jestem gotowy na polecenia. Napisz 'wyjdz' aby zakończyć.")
        while True:
            try:
                user_input = input("\n[Użytkownik] ").strip()
            except (EOFError, KeyboardInterrupt):  # pragma: no cover - interaktywne
                print("\n[Agent] Kończę pracę. Do zobaczenia!")
                break

            if not user_input:
                print("[Agent] Nie otrzymałem polecenia. Spróbuj ponownie.")
                continue

            if user_input.lower() in {"wyjdz", "exit", "quit"}:
                print("[Agent] Kończę pętlę na Twoje polecenie.")
                break

            command_text, metadata_extra = self._extract_metadata(user_input)
            metadata = {
                "source": "cli",
                "timestamp": datetime.now(timezone.utc).strftime(ISO8601),
                **metadata_extra,
            }
            response = self.process(command_text, metadata=metadata)
            print(f"[Agent] {response.message}")

    def _build_message(self, results: list[TaskResult], notes: list[str]) -> str:
        if not results:
            return "Nie utworzono żadnych zadań."

        successes = sum(1 for result in results if result.success)
        failures = len(results) - successes
        components = []

        if successes:
            components.append(f"Udało się wykonać {successes} zadania.")
        if failures:
            components.append(f"{failures} zadań zakończyło się błędem.")

        if notes:
            components.append("Uwagi: " + " ".join(notes))

        errors = [result.error for result in results if result.error]
        if errors:
            components.append("Błędy: " + " | ".join(filter(None, errors)))

        return " ".join(components)

    @staticmethod
    def _resolve_timestamp(metadata: Dict) -> datetime:
        value = metadata.get("timestamp")
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc)
        if isinstance(value, str):
            try:
                return datetime.strptime(value, ISO8601).astimezone(timezone.utc)
            except ValueError:
                logger.debug("Nie udało się sparsować znacznika czasu '%s'", value)
        return datetime.now(timezone.utc)

    @staticmethod
    def _configure_logging() -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )

    @staticmethod
    def _extract_metadata(raw_input: str) -> Tuple[str, Dict]:
        raw = raw_input.strip()
        if not raw:
            return raw, {}

        # Obsługa separatora "|" lub JSON na końcu
        if "|" in raw:
            command_part, metadata_part = raw.rsplit("|", 1)
            command_part = command_part.strip()
            metadata_part = metadata_part.strip()
            metadata = AgentLoop._try_parse_json(metadata_part)
            if metadata is not None:
                return command_part, metadata

        if raw.endswith("}") and "{" in raw:
            brace_index = raw.rfind("{")
            metadata_candidate = raw[brace_index:]
            metadata = AgentLoop._try_parse_json(metadata_candidate)
            if metadata is not None:
                return raw[:brace_index].strip(), metadata

        return raw, {}

    @staticmethod
    def _try_parse_json(text: str) -> Optional[Dict]:
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            logger.debug("Nie udało się sparsować metadanych JSON: %s", text)
        return None
