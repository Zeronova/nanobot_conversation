"""Constants for the Nanobot Conversation integration."""

import logging

from homeassistant.const import CONF_LLM_HASS_API, CONF_PROMPT
from homeassistant.helpers import llm

DOMAIN = "nanobot_conversation"
LOGGER = logging.getLogger(__package__)

CONF_API_URL = "api_url"
CONF_MODEL = "model"
CONF_RECOMMENDED = "recommended"

DEFAULT_API_URL = "http://localhost:8900"
DEFAULT_MODEL = ""

RECOMMENDED_CONVERSATION_OPTIONS = {
    CONF_RECOMMENDED: True,
    CONF_LLM_HASS_API: [llm.LLM_API_ASSIST],
    CONF_PROMPT: llm.DEFAULT_INSTRUCTIONS_PROMPT,
}
