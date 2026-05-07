# Nanobot Conversation Agent

Ein benutzerdefinierter Conversation Agent für Home Assistant, der eine Verbindung zur **Nanobot AI API** herstellt.

Ermöglicht dir, mit deinem lokalen KI-Assistenten via Home Assistant zu chatten – inklusive Tool/Device-Steuerung direkt aus dem Gespräch heraus.

## Features

- 🤖 Nutzt die OpenAI-kompatible API von Nanobot (localhost:8900)
- 🛠️ Vollständige Tool-Unterstützung – steuere Geräte per Sprachbefehl
- 🔒 Läuft lokal, keine Cloud-Abhängigkeit
- ⚡ Konfigurierbar via Home Assistant UI (Config Flow)
- 📱 Funktioniert mit der Companion App, Voice Pipelines und Automatisierungen

## Installation

### Via HACS (empfohlen)

1. HACS → Custom Repositories → Repository hinzufügen
2. URL: `https://github.com/Zeronova/nanobot_conversation`
3. Kategorie: **Integration**
4. HACS durchsuchen → "Nanobot Conversation Agent" → Installieren
5. Home Assistant neu starten

### Manuell

1. Kopiere `custom_components/nanobot_conversation/` in dein HA `custom_components/` Verzeichnis
2. Home Assistant neu starten

## Konfiguration

1. Einstellungen → Geräte & Dienste → Integration hinzufügen
2. Nach "Nanobot Conversation Agent" suchen
3. API-URL eingeben (Standard: `http://localhost:8900/v1`)
4. Bestätigen – fertig.

## Voraussetzungen

- Home Assistant 2026.4 oder neuer
- [Nanobot](https://github.com/your-repo/nanobot) läuft lokal (API auf Port 8900)
- Python 3.14+

## Lizenz

MIT
