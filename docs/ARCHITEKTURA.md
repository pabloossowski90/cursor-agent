## Przegląd systemu

Agent reaguje wyłącznie na polecenia użytkownika przesyłane w języku naturalnym. Każde polecenie trafia do pętli sterującej, która rejestruje kontekst (czas, źródło, meta-cel), przekształca polecenie na strukturę zadań JSON i wysyła je do odpowiednich kontenerów serwisowych (STT, TTS, kontenery pomocnicze). Odpowiedzi są zwracane użytkownikowi po polsku wraz z informacją o postępie.

### Założenia środowiskowe
- Ubuntu Server 24.04 LTS, 10 GB RAM, 2 vCPU.
- Agent działa jako proces CLI/daemon uruchomiony na VPS.
- Kontenery (TTS, STT, inne narzędzia) udostępniają lokalne interfejsy HTTP przyjmujące i zwracające JSON.

## Składniki

### `AgentLoop`
- Uruchamia pętlę główną, zbiera polecenia od użytkownika i wywołuje dalsze komponenty.
- Zapobiega autonomicznym działaniom: czeka na polecenie i dopiero wtedy podejmuje akcję.

### `CommandRouter`
- Analizuje tekst polecenia i na podstawie prostych reguł/klasyfikacji intencji tworzy listę zadań (`Task`).
- Zadania zawierają docelowy kontener (`target`), akcję (`action`) oraz ładunek JSON (`payload`).

### `ContainerManager`
- Utrzymuje klientów HTTP do poszczególnych kontenerów (`TTSContainerClient`, `STTContainerClient`, `AuxContainerClient`).
- Odpowiada za wysyłanie żądań JSON, obsługę błędów i zbieranie odpowiedzi.
- Pozwala inicjować dodatkowe kontenery (np. N8N) na podstawie zadania `start_container`.

### `AgentState`
- Przechowuje meta-cel długoterminowy, historię poleceń, wykonane zadania oraz ostatnie odpowiedzi.
- Zawiera logger zdarzeń (czas, źródło, rezultat) wykorzystywany do raportowania postępów.

## Przepływ danych
1. Użytkownik przekazuje polecenie (np. tekst z czatu lub wynik STT) wraz z metadanymi czasu.
2. `AgentLoop` normalizuje dane i przekazuje do `CommandRouter`.
3. Router tworzy jedną lub wiele struktur `Task`.
4. `ContainerManager` wysyła zadania w formacie JSON do właściwych kontenerów i odbiera odpowiedzi.
5. `AgentState` aktualizuje historię i kontekst.
6. Agent formułuje odpowiedź w języku polskim, zwraca ją użytkownikowi i loguje wynik.

## Format JSON zadań

```json
{
  "task_id": "uuid",
  "meta_goal": "utrzymuj reaktywnego asystenta",
  "timestamp": "2025-10-30T12:34:56.789Z",
  "target": "tts",
  "action": "speak_text",
  "payload": {
    "text": "Dzień dobry!"
  },
  "context": {
    "user_id": "operator",
    "conversation_id": "2025-10-30"
  }
}
```

Odpowiedź kontenera powinna mieć analogiczny znacznik `task_id` i sekcję `result`.

## Bezpieczeństwo i odporność
- Błędy przy wywołaniu kontenerów nie zatrzymują pętli — agent raportuje problem i czeka na kolejne polecenie.
- Wywołania HTTP mają limit czasu (domyślnie 10 s) i mechanizm powtórzenia (limit 3 prób).
- Historia przechowywana jest w pamięci oraz opcjonalnie zapisywana do pliku JSON (logowanie).

## Rozszerzenia
- Integracja z kolejkami (RabbitMQ, Redis Streams) dla skalowania.
- Podmiana routera na model LLM rozpoznający intencje.
- Integracja z bazą danych kontekstu (np. SQLite) dla trwałego przechowywania historii.
