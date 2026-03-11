"""Fan platform for Kolors Kult 8-step dimmer / fan regulator."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from . import KolorsKultConfigEntry
from .const import DEVICE_TYPE_STEP_DIMMER, DOMAIN
from .coordinator import KolorsKultCoordinator
from .models import KolorsKultDevice

_LOGGER = logging.getLogger(__name__)

# The 8-step dimmer uses speed values: 12.5, 25, 37.5, 50, 62.5, 75, 87.5, 100
# We map these to HA's percentage system via ordered named speeds
ORDERED_NAMED_FAN_SPEEDS = [
    "12.5", "25.0", "37.5", "50.0", "62.5", "75.0", "87.5", "100.0"
]


def api_speed_to_percentage(api_speed: float) -> int:
    """Convert Kolors API speed (12.5-100) to HA percentage (1-100).

    The API uses 8 discrete steps: 12.5, 25, 37.5, ..., 100.
    """
    if api_speed <= 0:
        return 0
    # Find the closest named speed
    closest = min(ORDERED_NAMED_FAN_SPEEDS, key=lambda s: abs(float(s) - api_speed))
    return ordered_list_item_to_percentage(ORDERED_NAMED_FAN_SPEEDS, closest)


def percentage_to_api_speed(percentage: int) -> float:
    """Convert HA percentage (1-100) to Kolors API speed (12.5-100)."""
    if percentage <= 0:
        return 0.0
    named_speed = percentage_to_ordered_list_item(ORDERED_NAMED_FAN_SPEEDS, percentage)
    return float(named_speed)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KolorsKultConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kolors Kult fan entities from a config entry."""
    coordinator = entry.runtime_data

    entities = [
        KolorsKultFan(coordinator, device_id)
        for device_id, device in coordinator.data.items()
        if device.device_type == DEVICE_TYPE_STEP_DIMMER
    ]

    async_add_entities(entities)


class KolorsKultFan(CoordinatorEntity[KolorsKultCoordinator], FanEntity):
    """Representation of a Kolors Kult 8-step dimmer as a fan entity."""

    _attr_has_entity_name = True
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )
    _attr_speed_count = len(ORDERED_NAMED_FAN_SPEEDS)  # 8 speed steps

    def __init__(
        self,
        coordinator: KolorsKultCoordinator,
        device_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        device = coordinator.data[device_id]

        self._attr_unique_id = f"{DOMAIN}_{device_id}"
        self._attr_name = f"{device.controller_product_id} {device.name}"
        # Remember last non-zero speed so turn_on can restore it
        self._last_nonzero_speed: float = device.speed if device.speed > 0 else 100.0

        # Group devices under their controller (physical switch panel)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.controller_product_id)},
            name=f"Kolors Kult {device.controller_product_id}",
            manufacturer="Kolors India",
            model="Kult Smart Switch",
        )

    @property
    def _device(self) -> KolorsKultDevice | None:
        """Get the current device data from the coordinator."""
        return self.coordinator.data.get(self._device_id)

    @property
    def available(self) -> bool:
        """Return True if the device is available."""
        return super().available and self._device is not None

    @property
    def is_on(self) -> bool | None:
        """Return true if the fan is on."""
        device = self._device
        if device is None:
            return None
        return device.status

    @property
    def percentage(self) -> int | None:
        """Return the current speed as a percentage."""
        device = self._device
        if device is None:
            return None
        if not device.status:
            return 0
        return api_speed_to_percentage(device.speed)

    def _build_dimmer_settings(self, *, on: bool, speed: float) -> dict[str, Any]:
        """Build the settings dict for a dimmer mutation."""
        device = self._device
        steps = device.steps if device else 8
        return {
            "speed": speed,
            "status": on,
            "child_lock": False,
            "steps": steps,
            "index": 0,
            "state": 0,
        }

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        if percentage == 0:
            await self.async_turn_off()
            return

        api_speed = percentage_to_api_speed(percentage)
        self._last_nonzero_speed = api_speed
        settings = self._build_dimmer_settings(on=True, speed=api_speed)
        await self.coordinator.send_and_refresh(self._device_id, settings)

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn the fan on.

        If a percentage is given, use that speed.
        Otherwise restore the last non-zero speed, or 100% if none.
        """
        if percentage is not None:
            await self.async_set_percentage(percentage)
            return

        # Use last known non-zero speed, defaulting to 100%
        speed = self._last_nonzero_speed
        settings = self._build_dimmer_settings(on=True, speed=speed)
        await self.coordinator.send_and_refresh(self._device_id, settings)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""
        # Remember current speed before turning off so turn_on can restore it
        device = self._device
        if device and device.speed > 0:
            self._last_nonzero_speed = device.speed

        settings = self._build_dimmer_settings(on=False, speed=0.0)
        await self.coordinator.send_and_refresh(self._device_id, settings)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Keep _last_nonzero_speed in sync when data arrives from polling
        device = self._device
        if device and device.speed > 0:
            self._last_nonzero_speed = device.speed
        self.async_write_ha_state()
