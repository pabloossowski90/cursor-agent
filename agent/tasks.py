from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


ISO8601 = "%Y-%m-%dT%H:%M:%S.%fZ"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class UserCommand:
    text: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "timestamp": self.timestamp.strftime(ISO8601),
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class Task:
    target: str
    action: str
    payload: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    task_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)

    def to_json(self, meta_goal: str) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "meta_goal": meta_goal,
            "timestamp": self.created_at.strftime(ISO8601),
            "target": self.target,
            "action": self.action,
            "payload": self.payload,
            "context": self.context,
        }


@dataclass(slots=True)
class TaskResult:
    task: Task
    success: bool
    response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    attempts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task.to_json(meta_goal=""),
            "success": self.success,
            "response": self.response,
            "error": self.error,
            "attempts": self.attempts,
        }


@dataclass(slots=True)
class AgentResponse:
    message: str
    tasks: List[Task]
    results: List[TaskResult]
    state_snapshot: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message,
            "tasks": [task.to_json(meta_goal=self.state_snapshot.get("meta_goal", "")) for task in self.tasks],
            "results": [result.to_dict() for result in self.results],
            "state_snapshot": self.state_snapshot,
        }
