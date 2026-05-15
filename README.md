# Nanobot Conversation Agent für Home Assistant

Home Assistant Conversation Agent, der über eine OpenAI-kompatible API mit dem [nanobot](https://github.com/zeronova/nanobot) AI Assistant kommuniziert. Ermöglicht Sprachsteuerung und Tool-Calling via HA Assist.

## Installation

### Via HACS (empfohlen)

1. HACS → Custom Repositories → `https://github.com/zeronova/HA_nanobot_conversation` (Typ: Integration)
2. HACS → Integrationen → "Nanobot Conversation" installieren
3. HA neu starten

### Manuell

1. Ordner `nanobot_conversation` nach `custom_components/nanobot_conversation` kopieren
2. HA neu starten

## Konfiguration

1. **Integration hinzufügen:** Einstellungen → Geräte & Dienste → Integration hinzufügen → "Nanobot Conversation"
2. **API-URL** eintragen (Standard: `http://localhost:8900`)
3. **Assistent einrichten:** Einstellungen → Sprachassistenten → Assist → Konversationsagent → "Nanobot Conversation" auswählen
