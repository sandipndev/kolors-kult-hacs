"""Data update coordinator for Kolors Kult."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import KolorsKultApi, KolorsKultApiError, KolorsKultAuthError
from .const import DOMAIN, UPDATE_INTERVAL
from .models import KolorsKultDevice, parse_devices

_LOGGER = logging.getLogger(__name__)


class KolorsKultCoordinator(DataUpdateCoordinator[dict[str, KolorsKultDevice]]):
    """Coordinator to manage fetching Kolors Kult device data.

    Uses a lock to ensure mutations are sent one at a time (the API
    does not support concurrent writes).  After every mutation the
    coordinator re-fetches the full device list so the caller blocks
    until the confirmed state is available.
    """

    def __init__(self, hass: HomeAssistant, api: KolorsKultApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.api = api
        self._mutation_lock = asyncio.Lock()

    async def _async_update_data(self) -> dict[str, KolorsKultDevice]:
        """Fetch data from the Kolors Kult API."""
        try:
            raw_data = await self.api.get_devices()
            return parse_devices(raw_data)
        except KolorsKultAuthError:
            _LOGGER.debug("Token expired, re-authenticating")
            try:
                await self.api.authenticate()
                raw_data = await self.api.get_devices()
                return parse_devices(raw_data)
            except KolorsKultApiError as err:
                raise UpdateFailed(
                    f"Re-authentication failed: {err}"
                ) from err
        except KolorsKultApiError as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

    async def send_and_refresh(
        self, device_id: str, settings: dict[str, Any]
    ) -> None:
        """Send a single mutation then reload confirmed state.

        Acquires a lock so mutations are strictly serialized.
        The caller will block until the fresh state is available,
        which keeps the HA UI in a loading/spinner state until done.
        """
        async with self._mutation_lock:
            await self.api.update_device_settings(device_id, settings)
            await self.async_refresh()
