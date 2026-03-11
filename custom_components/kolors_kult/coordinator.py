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
        """Send a single mutation then poll until the confirmed state matches.

        Acquires a lock so mutations are strictly serialized.
        After sending the mutation, polls the load endpoint until the
        device's status/speed reflect what we sent, or gives up after
        a timeout.  The caller blocks the whole time so the HA UI
        stays in a loading/spinner state.
        """
        desired_status = settings.get("status")
        desired_speed = settings.get("speed")

        async with self._mutation_lock:
            await self.api.update_device_settings(device_id, settings)

            # Poll until the device state matches what we just sent
            max_attempts = 10
            for attempt in range(max_attempts):
                await asyncio.sleep(1)
                await self.async_refresh()

                device = self.data.get(device_id) if self.data else None
                if device is None:
                    continue

                status_ok = device.status == desired_status
                # For speed: only check when turning on (speed matters)
                # When turning off, status match is sufficient
                if desired_status is False:
                    if status_ok:
                        return
                else:
                    speed_ok = (
                        desired_speed is None
                        or abs(device.speed - desired_speed) < 1.0
                    )
                    if status_ok and speed_ok:
                        return

            _LOGGER.warning(
                "Device %s did not confirm state after %d attempts",
                device_id,
                max_attempts,
            )
