"""Constants for the Nanobot Conversation integration."""

import logging

from homeassistant.const import CONF_PROMPT
from homeassistant.helpers.llm import DEFAULT_INSTRUCTIONS_PROMPT

DOMAIN = "nanobot_conversation"
LOGGER = logging.getLogger(__package__)

CONF_API_URL = "api_url"
CONF_MODEL = "model"
CONF_MAX_TOKENS = "max_tokens"
CONF_TEMPERATURE = "temperature"
CONF_TOP_P = "top_p"

DEFAULT_API_URL = "http://localhost:8900"
DEFAULT_MODEL = ""
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.3
DEFAULT_TOP_P = 0.9

MAX_TOKENS_UPPER_BOUND = 16384

RECOMMENDED_CONVERSATION_OPTIONS = {
    CONF_MODEL: DEFAULT_MODEL,
    CONF_PROMPT: DEFAULT_INSTRUCTIONS_PROMPT,
    CONF_MAX_TOKENS: DEFAULT_MAX_TOKENS,
    CONF_TEMPERATURE: DEFAULT_TEMPERATURE,
    CONF_TOP_P: DEFAULT_TOP_P,
}
