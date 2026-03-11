"""Switch platform for Kolors Kult buttons."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import KolorsKultConfigEntry
from .const import DEVICE_TYPE_BUTTON, DOMAIN
from .coordinator import KolorsKultCoordinator
from .models import KolorsKultDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KolorsKultConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kolors Kult switch entities from a config entry."""
    coordinator = entry.runtime_data

    entities = [
        KolorsKultSwitch(coordinator, device_id)
        for device_id, device in coordinator.data.items()
        if device.device_type == DEVICE_TYPE_BUTTON
    ]

    async_add_entities(entities)


class KolorsKultSwitch(CoordinatorEntity[KolorsKultCoordinator], SwitchEntity):
    """Representation of a Kolors Kult button as a switch."""

    _attr_has_entity_name = True
    _attr_device_class = SwitchDeviceClass.SWITCH

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
        """Return true if the switch is on."""
        device = self._device
        if device is None:
            return None
        return device.status

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.coordinator.api.set_button_state(self._device_id, True)
        # Optimistic update for snappy UI
        device = self._device
        if device:
            device.status = True
            self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.coordinator.api.set_button_state(self._device_id, False)
        # Optimistic update for snappy UI
        device = self._device
        if device:
            device.status = False
            self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
