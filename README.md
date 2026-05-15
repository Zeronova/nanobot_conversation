# Nanobot Conversation Agent für Home Assistant

Home Assistant Conversation Agent, der über OpenAI-kompatible API mit dem [nanobot](https://github.com/zeronova/nanobot) AI Assistant kommuniziert.

## Features

- Vollständiger Conversation Agent (Sprachsteuerung via Assist)
- Tool-Calling (HA-Integrationen via LLM API)
- Sitzungsverwaltung via `session_id`
- Konfigurierbares Prompt-System, Modell-Parameter und API-Endpunkt

## Installation

### Via HACS (empfohlen)

1. HACS → Custom Repositories hinzufügen: `https://github.com/zeronova/HA_nanobot_conversation`
2. Typ: "Integration"
3. HACS → Integrationen → "Nanobot Conversation" suchen und installieren
4. HA neu starten

### Manuell

1. Ordner `nanobot_conversation` nach `custom_components/nanobot_conversation` kopieren
2. HA neu starten

### Konfiguration

1. Integration über Einstellungen → Geräte & Dienste → Integration hinzufügen → "Nanobot Conversation" konfigurieren
2. API-URL eintragen (Standard: `http://localhost:8900`)
3. Assistant-Sprachagent auf "Nanobot Conversation" setzen

## Konfiguration

| Option | Standard | Beschreibung |
|--------|----------|-------------|
| API URL | `http://localhost:8900` | Nanobot-Serve-Endpoint |
| Prompt | HA Default | System-Prompt für den Agent |
| Model | `""` (Server-Standard) | OpenAI-Modell-Override |
| Max Tokens | 4096 | Maximale Antwortlänge |
| Temperature | 0.3 | Kreativität (0.0–2.0) |
| Top P | 0.9 | Nucleus Sampling |
| Conversation ID | leer | Session-Tracking (automatisch) |

## Funktionsweise

Der Agent fasst System- und User-Prompt zu einer einzelnen User-Nachricht zusammen (nanobot serve akzeptiert nur single-user messages). Tool-Aufrufe werden in einer Schleife bis zu 10 Iterationen verarbeitet.

## Entwicklung

- `conversation.py` — Hauptlogik des Conversation Agent
- `config_flow.py` — Setup-/Options-Flow
- `const.py` — Konstanten und Standardwerte
- `__init__.py` — Plattform-Setup
