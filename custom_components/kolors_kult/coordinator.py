"""Data update coordinator for Kolors Kult."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import KolorsKultApi, KolorsKultApiError, KolorsKultAuthError
from .const import DOMAIN, UPDATE_INTERVAL
from .models import KolorsKultDevice, parse_devices

_LOGGER = logging.getLogger(__name__)


class KolorsKultCoordinator(DataUpdateCoordinator[dict[str, KolorsKultDevice]]):
    """Coordinator to manage fetching Kolors Kult device data."""

    def __init__(self, hass: HomeAssistant, api: KolorsKultApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.api = api

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
