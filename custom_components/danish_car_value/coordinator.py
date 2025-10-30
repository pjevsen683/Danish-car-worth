"""Data coordinator for the Danish Car Value integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import TjekBilClient, TjekBilError
from .const import UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class DanishCarValueCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that fetches valuation data once per day."""

    def __init__(self, hass: HomeAssistant, plate: str) -> None:
        normalised = plate.replace(" ", "").replace("-", "").upper()
        self._plate = normalised
        self.plate = self._plate
        session = async_get_clientsession(hass)
        self._client = TjekBilClient(session)
        super().__init__(
            hass,
            _LOGGER,
            name=f"Danish car value ({self._plate})",
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            vehicle_data = await self._client.async_get_vehicle_by_plate(self._plate)
        except TjekBilError as exc:
            raise UpdateFailed(f"Failed to look up plate {self._plate}: {exc}") from exc

        dmr_id = (vehicle_data.get("basic") or {}).get("koeretoejId")
        if dmr_id is None:
            raise UpdateFailed(
                f"No DMR id found for license plate {self._plate}"  # type: ignore[arg-type]
            )

        try:
            valuation_data = await self._client.async_get_valuation(int(dmr_id))
        except TjekBilError as exc:
            raise UpdateFailed(f"Failed to load valuation for {self._plate}: {exc}") from exc

        valuation_data["dmr_id"] = int(dmr_id)
        valuation_data["plate"] = self._plate
        valuation_data["vehicle"] = vehicle_data
        return valuation_data
