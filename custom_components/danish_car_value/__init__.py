"""Home Assistant integration for Danish car valuation via TjekBil."""

from __future__ import annotations

DOMAIN = "danish_car_value"


async def async_setup(hass, config):
    """Set up the integration from YAML."""
    return True


async def async_setup_entry(hass, entry):
    """Set up the integration from Config Entry (not used)."""
    return True


async def async_unload_entry(hass, entry):
    """Unload the integration from Config Entry (not used)."""
    return True
