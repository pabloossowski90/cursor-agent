# Reaktywny agent kontenerowy

Projekt przedstawia agenta CLI działającego na VPS z Ubuntu 24.04 LTS (10 GB RAM / 2 vCPU). Agent reaguje na polecenia użytkownika, tłumaczy je na zadania JSON i wysyła do lokalnych kontenerów usługowych (TTS/STT/kontenery pomocnicze).

## Funkcje
- Interpretacja poleceń w języku naturalnym i zamiana na zadania JSON.
- Obsługa kontenerów TTS, STT oraz kontenerów pomocniczych przez HTTP/JSON.
- Pętla reaktywna działająca tylko na wyraźne polecenia użytkownika.
- Utrzymywanie meta-celu i historii działań (logowanie zdarzeń z znacznikami czasu).
- Tryb `dry-run` pozwalający testować bez realnych kontenerów.

## Struktura projektu
- `agent/config.py` – obsługa konfiguracji agenta i kontenerów.
- `agent/context.py` – stan, historia i logowanie zdarzeń.
- `agent/router.py` – mapowanie poleceń na zadania JSON.
- `agent/containers.py` – komunikacja HTTP z kontenerami i zarządzanie nimi.
- `agent/loop.py` – pętla główna i interfejs użytkownika.
- `main.py` – punkt wejścia CLI.
- `docs/ARCHITEKTURA.md` – dokumentacja architektury.

## Wymagania
- Python 3.11+
- System Ubuntu 24.04 LTS (lub zgodny)
- Kontenery TTS/STT udostępniające endpoint HTTP JSON

## Instalacja
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uruchomienie
```bash
python main.py --config config/agent.config.json
```

Przy pierwszym uruchomieniu powstanie domyślna konfiguracja w trybie `dry-run`. Aby połączyć się z realnymi kontenerami, zaktualizuj adresy `base_url` i usuń/dostosuj flagę `dry_run`.

## Przykładowe polecenia
- `Powiedz: Dzień dobry z kontenera TTS.`
- `Transkrybuj nagranie spotkania` (w metadanych polecenia podaj `audio_path`).
- `Uruchom kontener n8n`.

### Polecenia z metadanymi (CLI)
W trybie CLI można dołączyć metadane w formacie JSON, np.:

```
Transkrybuj nagranie | {"audio_path": "/data/spotkanie.wav", "language": "pl-PL"}
```

Agent automatycznie doda znacznik czasu i przekaże metadane do kontenerów.

Agent raportuje wynik po polsku i loguje każde zadanie wraz z czasem.
