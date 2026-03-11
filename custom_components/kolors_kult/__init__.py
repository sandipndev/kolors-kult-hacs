"""The Kolors Kult integration for Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import KolorsKultApi
from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN, PLATFORMS
from .coordinator import KolorsKultCoordinator

_LOGGER = logging.getLogger(__name__)

type KolorsKultConfigEntry = ConfigEntry[KolorsKultCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: KolorsKultConfigEntry) -> bool:
    """Set up Kolors Kult from a config entry."""
    api = KolorsKultApi(
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
    )

    await api.authenticate()

    coordinator = KolorsKultCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: KolorsKultConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator: KolorsKultCoordinator = entry.runtime_data
        await coordinator.api.close()

    return unload_ok
