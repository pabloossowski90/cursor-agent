# Interfejs JSON agenta z kontenerami

## Ogólny format zapytania

```json
{
  "task_id": "uuid",
  "meta_goal": "utrzymuj reaktywnego asystenta obsługującego kontenery",
  "timestamp": "2025-10-30T12:34:56.789Z",
  "target": "tts",
  "action": "speak_text",
  "payload": {},
  "context": {}
}
```

- `task_id` – unikalny identyfikator zadania.
- `meta_goal` – meta-cel agenta przekazywany do kontenera (pozwala na kontekstualne działania).
- `timestamp` – czas utworzenia zadania w UTC.
- `target` – typ kontenera (`tts`, `stt`, `aux`, `operator`).
- `action` – nazwa akcji wykonywanej przez kontener.
- `payload` – dane specyficzne dla akcji.
- `context` – dodatkowe metadane (np. źródło polecenia, identyfikatory sesji).

## Kontener TTS
- Endpoint: `POST http://<HOST_TTS>:<PORT>/tasks`
- Akcje: `speak_text`

### Przykład
```json
{
  "task_id": "7aa3f9b6-1fd3-4d6a-8e2d-7b21a1d3c745",
  "meta_goal": "utrzymuj reaktywnego asystenta obsługującego kontenery",
  "timestamp": "2025-10-30T12:35:12.000Z",
  "target": "tts",
  "action": "speak_text",
  "payload": {
    "text": "Dzień dobry!",
    "voice": "pl-PL-EwaNeural"
  },
  "context": {
    "agent": "reactive-vps",
    "source": "cli"
  }
}
```

### Oczekiwana odpowiedź
```json
{
  "task_id": "7aa3f9b6-1fd3-4d6a-8e2d-7b21a1d3c745",
  "status": "done",
  "audio_path": "/tmp/output.wav"
}
```

## Kontener STT
- Endpoint: `POST http://<HOST_STT>:<PORT>/tasks`
- Akcje: `transcribe_audio`

### Przykład
```json
{
  "task_id": "bb842a09-0a3c-4d3b-a4cf-41b21e31b369",
  "meta_goal": "utrzymuj reaktywnego asystenta obsługującego kontenery",
  "timestamp": "2025-10-30T12:36:00.000Z",
  "target": "stt",
  "action": "transcribe_audio",
  "payload": {
    "audio": "/data/input.wav",
    "language": "pl-PL"
  },
  "context": {
    "agent": "reactive-vps",
    "source": "cli"
  }
}
```

### Oczekiwana odpowiedź
```json
{
  "task_id": "bb842a09-0a3c-4d3b-a4cf-41b21e31b369",
  "status": "done",
  "transcript": "Przykładowa transkrypcja",
  "confidence": 0.94
}
```

## Kontenery pomocnicze
- Endpoint: `POST http://<HOST_AUX>:<PORT>/tasks`
- Akcje: `manage_container`

### Przykład
```json
{
  "task_id": "1c8a26af-1c77-49c8-baf8-635ae798f47b",
  "meta_goal": "utrzymuj reaktywnego asystenta obsługującego kontenery",
  "timestamp": "2025-10-30T12:37:21.000Z",
  "target": "aux",
  "action": "manage_container",
  "payload": {
    "container": "n8n",
    "mode": "start"
  },
  "context": {
    "agent": "reactive-vps"
  }
}
```

### Oczekiwana odpowiedź
```json
{
  "task_id": "1c8a26af-1c77-49c8-baf8-635ae798f47b",
  "status": "started",
  "container": "n8n"
}
```

## Błędy i retry
- Odpowiedź z kodem HTTP >= 400 jest traktowana jako błąd i powtarzana zgodnie z parametrem `retries`.
- Po wyczerpaniu prób agent zwróci użytkownikowi komunikat o błędzie.
