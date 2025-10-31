"""Thin API client for TjekBil endpoints used by the integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import API_BASE_URL, API_OFFICIAL_BASE_URL, DEFAULT_HEADERS, REQUEST_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class TjekBilError(Exception):
    """Base exception for communication issues."""


class TjekBilClient:
    """Handle communication with tjekbil.dk."""

    def __init__(self, session: aiohttp.ClientSession, api_key: str | None = None) -> None:
        self._session = session
        self._api_key = api_key

    async def async_get_vehicle_by_plate(self, plate: str) -> dict[str, Any]:
        """Return DMR information (incl. koeretoejId) for a license plate."""

        if self._api_key:
            url = f"{API_OFFICIAL_BASE_URL}/v1/dmr/regnr/{plate}"
            headers = {"X-ApiKey": self._api_key}
        else:
            url = f"{API_BASE_URL}/api/v3/dmr/regnrnew/{plate}"
            headers = None

        return await self._async_request("GET", url, headers=headers)

    async def async_get_valuation(
        self,
        *,
        plate: str,
        dmr_id: int | None,
        mileage: int | None = None,
    ) -> dict[str, Any]:
        """Return valuation data using the best available endpoint."""

        if self._api_key:
            url = f"{API_OFFICIAL_BASE_URL}/vehiclevaluation/valuation"
            params: dict[str, str] = {"registrationNumber": plate}
            if mileage is not None:
                params["mileage"] = str(mileage)
            headers = {"X-ApiKey": self._api_key}
            return await self._async_request("GET", url, params=params, headers=headers)

        if dmr_id is None:
            raise TjekBilError("DMR id required when using public valuation endpoint")

        url = f"{API_BASE_URL}/api/v3/valuation/valuationdmr"
        return await self._async_request("POST", url, params={"dmrId": str(dmr_id)})

    async def _async_request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Execute an HTTP request and return JSON content."""

        req_headers = dict(DEFAULT_HEADERS)
        if headers:
            req_headers.update(headers)

        try:
            async with self._session.request(
                method,
                url,
                params=params,
                headers=req_headers,
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise TjekBilError(
                        f"Error {response.status} from {url} ({text[:200]})"
                    )

                return await response.json(content_type=None)

        except asyncio.TimeoutError as err:
            raise TjekBilError(f"Timeout communicating with {url}") from err
        except aiohttp.ClientError as err:
            raise TjekBilError(f"Error communicating with {url}: {err}") from err
