"""Constants for the Danish Car Value integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "danish_car_value"

CONF_LICENSE_PLATE = "plate"
DEFAULT_NAME = "Danish Car Value"

API_BASE_URL = "https://www.tjekbil.dk"

REQUEST_TIMEOUT = 30

UPDATE_INTERVAL = timedelta(days=1)

DEFAULT_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "HomeAssistant-DanishCarValue/0.1.0",
}
