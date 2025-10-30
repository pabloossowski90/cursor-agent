from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import re

from .tasks import Task, UserCommand


@dataclass(slots=True)
class RoutedCommand:
    command: UserCommand
    tasks: List[Task]
    notes: List[str]


class CommandRouter:
    """Prosty router poleceń na zadania JSON."""

    def __init__(self, default_context: Dict[str, str] | None = None) -> None:
        self.default_context = default_context or {}

    def route(self, command: UserCommand) -> RoutedCommand:
        text = command.text.lower().strip()
        tasks: List[Task] = []
        notes: List[str] = []

        # TTS
        if any(keyword in text for keyword in ["powiedz", "tts", "wypowiedz", "odtwórz", "odtworz"]):
            payload = {
                "text": command.metadata.get("text") or command.text,
                "voice": command.metadata.get("voice", "pl-PL-EwaNeural"),
            }
            context = {
                **self.default_context,
                "source": command.metadata.get("source", "cli"),
            }
            tasks.append(Task(target="tts", action="speak_text", payload=payload, context=context))
            notes.append("Wygenerowano zadanie TTS.")

        # STT - wymaga ścieżki do pliku audio lub identyfikatora strumienia
        stt_keywords = ["transkryb", "rozpoznaj mow", "rozpoznaj mowe", "stt"]
        if any(keyword in text for keyword in stt_keywords):
            audio_path = command.metadata.get("audio_path") or command.metadata.get("stream_id")
            if not audio_path:
                notes.append("Brak ścieżki audio w metadanych — pomijam STT.")
            else:
                payload = {
                    "audio": audio_path,
                    "language": command.metadata.get("language", "pl-PL"),
                }
                context = {
                    **self.default_context,
                    "source": command.metadata.get("source", "cli"),
                }
                tasks.append(Task(target="stt", action="transcribe_audio", payload=payload, context=context))
                notes.append("Wygenerowano zadanie STT.")

        # Kontenery pomocnicze (np. N8N)
        aux_match = re.search(r"odpal|uruchom|włącz|wlacz", text)
        if aux_match:
            container_name = command.metadata.get("container")
            if not container_name:
                # spróbuj rozpoznać nazwę z tekstu
                container_name = self._extract_container_name(text)
            if container_name:
                payload = {
                    "container": container_name,
                    "mode": command.metadata.get("mode", "start"),
                }
                tasks.append(Task(target="aux", action="manage_container", payload=payload, context=self.default_context))
                notes.append(f"Zadanie dla kontenera pomocniczego: {container_name}.")
            else:
                notes.append("Nie rozpoznano nazwy kontenera do uruchomienia.")

        if not tasks:
            # Fallback: poinformuj operatora, że polecenie nie zostało zmapowane
            tasks.append(
                Task(
                    target="operator",
                    action="notify",
                    payload={
                        "message": command.text,
                        "metadata": command.metadata,
                    },
                    context=self.default_context,
                )
            )
            notes.append("Polecenie przekierowano do operatora.")

        return RoutedCommand(command=command, tasks=tasks, notes=notes)

    @staticmethod
    def _extract_container_name(text: str) -> str | None:
        candidates = ["n8n", "test", "sandbox", "tts", "stt"]
        for candidate in candidates:
            if candidate in text:
                return candidate
        match = re.search(r"kontener ([a-z0-9-_]+)", text)
        if match:
            return match.group(1)
        return None
