from __future__ import annotations

from typing import Dict, Iterable, List, Optional
import logging

import requests
from requests import RequestException, Response

from .config import AgentConfig, ContainerConfig
from .tasks import Task, TaskResult


logger = logging.getLogger(__name__)


class ContainerClient:
    def __init__(self, config: ContainerConfig) -> None:
        self.config = config
        self.session = requests.Session()

    def dispatch(self, task: Task, meta_goal: str, dry_run: bool = False) -> TaskResult:
        payload = task.to_json(meta_goal)

        if not self.config.enabled:
            return TaskResult(task=task, success=False, error="Kontener wyłączony", attempts=0)

        if dry_run:
            logger.debug("Dry-run dla kontenera %s: %s", self.config.name, payload)
            return TaskResult(
                task=task,
                success=True,
                response={"status": "dry_run", "payload": payload},
                attempts=0,
            )

        last_error: Optional[str] = None
        for attempt in range(1, self.config.retries + 1):
            try:
                response = self.session.post(
                    self.config.base_url,
                    json=payload,
                    headers={**self.config.extra_headers, "Content-Type": "application/json"},
                    timeout=self.config.timeout,
                )
                response.raise_for_status()
                return TaskResult(
                    task=task,
                    success=True,
                    response=self._parse_response(response),
                    attempts=attempt,
                )
            except RequestException as exc:  # pragma: no cover - zależne od środowiska
                last_error = str(exc)
                logger.warning(
                    "Błąd podczas wywołania kontenera %s (próba %s/%s): %s",
                    self.config.name,
                    attempt,
                    self.config.retries,
                    last_error,
                )
        return TaskResult(task=task, success=False, error=last_error, attempts=self.config.retries)

    @staticmethod
    def _parse_response(response: Response) -> Dict:
        try:
            return response.json()
        except ValueError:  # pragma: no cover - zależne od środowiska
            return {"status": "ok", "raw": response.text}


class ContainerManager:
    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.clients: Dict[str, ContainerClient] = {
            name: ContainerClient(cfg) for name, cfg in config.containers.items()
        }

    def dispatch_task(self, task: Task) -> TaskResult:
        if task.target == "operator":
            return TaskResult(
                task=task,
                success=True,
                response={"status": "operator_notified", "message": task.payload.get("message")},
                attempts=0,
            )

        client = self.clients.get(task.target)
        if not client:
            return TaskResult(task=task, success=False, error=f"Brak klienta dla celu '{task.target}'", attempts=0)

        return client.dispatch(task, meta_goal=self.config.meta_goal, dry_run=self.config.dry_run)

    def dispatch_many(self, tasks: Iterable[Task]) -> List[TaskResult]:
        return [self.dispatch_task(task) for task in tasks]
