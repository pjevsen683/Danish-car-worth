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

    def __init__(
        self,
        hass: HomeAssistant,
        plate: str,
        *,
        api_key: str | None = None,
        mileage: int | None = None,
    ) -> None:
        normalised = plate.replace(" ", "").replace("-", "").upper()
        self._plate = normalised
        self.plate = self._plate
        self._mileage = mileage
        session = async_get_clientsession(hass)
        self._client = TjekBilClient(session, api_key)
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

        dmr_int = int(dmr_id) if dmr_id is not None else None

        try:
            valuation_data = await self._client.async_get_valuation(
                plate=self._plate,
                dmr_id=dmr_int,
                mileage=self._mileage,
            )
        except TjekBilError as exc:
            raise UpdateFailed(f"Failed to load valuation for {self._plate}: {exc}") from exc

        if "averagePrice" not in valuation_data:
            low = valuation_data.get("low")
            high = valuation_data.get("high")
            if isinstance(low, (int, float)) and isinstance(high, (int, float)):
                valuation_data["averagePrice"] = (float(low) + float(high)) / 2

        if dmr_int is not None:
            valuation_data.setdefault("dmr_id", dmr_int)
        valuation_data["plate"] = self._plate
        valuation_data["vehicle"] = vehicle_data
        valuation_data["requestedMileage"] = self._mileage
        return valuation_data
