from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from .tasks import TaskResult, UserCommand, ISO8601


@dataclass(slots=True)
class HistoryEntry:
    timestamp: datetime
    event: str
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.strftime(ISO8601),
            "event": self.event,
            "payload": self.payload,
        }


@dataclass(slots=True)
class AgentState:
    meta_goal: str
    history: List[HistoryEntry] = field(default_factory=list)
    last_results: List[TaskResult] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    def log_event(self, event: str, payload: Optional[Dict[str, Any]] = None) -> None:
        self.history.append(
            HistoryEntry(
                timestamp=datetime.now(timezone.utc),
                event=event,
                payload=payload or {},
            )
        )

    def record_command(self, command: UserCommand) -> None:
        self.log_event(
            "user_command",
            {
                "text": command.text,
                "metadata": command.metadata,
                "timestamp": command.timestamp.strftime(ISO8601),
            },
        )

    def record_results(self, results: List[TaskResult]) -> None:
        self.last_results = results
        for result in results:
            event = "task_success" if result.success else "task_error"
            self.log_event(
                event,
                {
                    "task_id": result.task.task_id,
                    "target": result.task.target,
                    "action": result.task.action,
                    "payload": result.task.payload,
                    "error": result.error,
                },
            )

    def to_snapshot(self) -> Dict[str, Any]:
        return {
            "meta_goal": self.meta_goal,
            "last_results": [result.to_dict() for result in self.last_results],
            "history_tail": [entry.to_dict() for entry in self.history[-20:]],
            "meta": self.meta,
        }

    def dump_history(self, path: Path) -> None:
        data = [entry.to_dict() for entry in self.history]
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
