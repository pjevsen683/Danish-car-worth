"""Sensor platform for the Danish Car Value integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import ATTR_ATTRIBUTION, CONF_NAME, CURRENCY_DKK
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity, UpdateFailed
from homeassistant.exceptions import PlatformNotReady

from .const import CONF_LICENSE_PLATE, DEFAULT_NAME, DOMAIN
from .coordinator import DanishCarValueCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class DanishCarValueSensorEntityDescription(SensorEntityDescription):
    """Entity description with metadata for the integration."""


SENSOR_DESCRIPTIONS: tuple[DanishCarValueSensorEntityDescription, ...] = (
    DanishCarValueSensorEntityDescription(
        key="low",
        name="Minimum price",
        icon="mdi:cash-minus",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY_DKK,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    DanishCarValueSensorEntityDescription(
        key="averagePrice",
        name="Average price",
        icon="mdi:cash",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY_DKK,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    DanishCarValueSensorEntityDescription(
        key="high",
        name="Maximum price",
        icon="mdi:cash-plus",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY_DKK,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_LICENSE_PLATE): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensors from YAML configuration."""

    plate: str = config[CONF_LICENSE_PLATE]
    base_name: str = config.get(CONF_NAME, DEFAULT_NAME)

    coordinator = DanishCarValueCoordinator(hass, plate)
    try:
        await coordinator.async_config_entry_first_refresh()
    except UpdateFailed as err:
        raise PlatformNotReady(err) from err

    entities: list[DanishCarValueSensor] = []
    normalised_plate = coordinator.plate
    for description in SENSOR_DESCRIPTIONS:
        entity_name = f"{base_name} {description.name} ({normalised_plate})"
        entities.append(
            DanishCarValueSensor(
                coordinator,
                description,
                name=entity_name,
            )
        )

    async_add_entities(entities)


class DanishCarValueSensor(CoordinatorEntity[dict[str, Any]], SensorEntity):
    """Representation of a single valuation datapoint."""

    entity_description: DanishCarValueSensorEntityDescription

    def __init__(
        self,
        coordinator: DanishCarValueCoordinator,
        description: DanishCarValueSensorEntityDescription,
        *,
        name: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = name
        self._attr_should_poll = False
        plate = coordinator.data.get("plate") or coordinator.plate
        self._plate = str(plate).upper()
        self._attr_unique_id = f"{self._plate}_{description.key}".lower()

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data or {}
        value = data.get(self.entity_description.key)
        if value is None:
            return None
        try:
            return round(float(value))
        except (TypeError, ValueError):
            _LOGGER.debug("Unable to parse valuation value %s", value)
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        vehicle = (data.get("vehicle") or {}).get("basic") or {}
        return {
            ATTR_ATTRIBUTION: "Data courtesy of tjekbil.dk",
            "plate": data.get("plate"),
            "search_url": data.get("searchUrl"),
            "price_count": data.get("priceCount"),
            "average_mileage": data.get("averageMileage"),
            "headline": data.get("headline"),
            "failed_message": data.get("failedMessage"),
            "mileage": data.get("mileage"),
            "brand": vehicle.get("maerkeTypeNavn"),
            "model": vehicle.get("modelTypeNavn"),
            "variant": vehicle.get("variantTypeNavn"),
        }

    @property
    def device_info(self) -> DeviceInfo:
        data = self.coordinator.data or {}
        plate = data.get("plate", self._plate)
        vehicle = (data.get("vehicle") or {}).get("basic") or {}
        brand = vehicle.get("maerkeTypeNavn")
        model = vehicle.get("modelTypeNavn")
        name_parts = [part for part in (brand, model) if part]
        device_name = " ".join(name_parts) if name_parts else f"Vehicle {plate}"
        return DeviceInfo(
            identifiers={(DOMAIN, str(plate))},
            name=device_name,
            manufacturer=brand,
            model=model,
            configuration_url=f"https://www.tjekbil.dk/nummerplade/{plate}/overblik"
            if plate
            else None,
        )
