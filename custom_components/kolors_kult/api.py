"""API client for Kolors Kult cloud service (api.kolorsworld.net)."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import API_BASE_URL

_LOGGER = logging.getLogger(__name__)


class KolorsKultApiError(Exception):
    """Exception for API errors."""


class KolorsKultAuthError(KolorsKultApiError):
    """Exception for authentication errors."""


class KolorsKultApi:
    """API client for Kolors Kult (api.kolorsworld.net)."""

    def __init__(self, email: str, password: str) -> None:
        self._email = email
        self._password = password
        self._session: aiohttp.ClientSession | None = None
        self._token: str | None = None

    @property
    def token(self) -> str | None:
        """Return the current auth token."""
        return self._token

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "Origin": "https://api.kolorsworld.net/app/1.3/",
                    "Accept": "application/json",
                    "Accept-Language": "en-IN,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "User-Agent": "SkyBot.FormsApp/1.4.1 CFNetwork/3860.400.51 Darwin/25.3.0",
                    "Connection": "keep-alive",
                }
            )
        return self._session

    async def authenticate(self) -> dict[str, Any]:
        """Authenticate with the Kolors Kult API.

        POST /app/1.3/auth/login
        Body: {"email": "...", "password": "..."}
        Returns user data including token and product_ids.
        """
        session = await self._get_session()
        url = f"{API_BASE_URL}/auth/login"
        payload = {"email": self._email, "password": self._password}

        try:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()

                if not data.get("success"):
                    msg = data.get("message", {}).get(
                        "description", "Authentication failed"
                    )
                    raise KolorsKultAuthError(msg)

                self._token = data["data"]["token"]
                _LOGGER.debug("Authenticated successfully, token obtained")
                return data["data"]

        except aiohttp.ClientError as err:
            raise KolorsKultApiError(f"Connection error: {err}") from err

    async def get_devices(self) -> dict[str, Any]:
        """Fetch all devices from the API.

        GET /app/1.3/user/load?token=...
        Returns full controller/receiver/device hierarchy.
        """
        if not self._token:
            raise KolorsKultAuthError("Not authenticated")

        session = await self._get_session()
        url = f"{API_BASE_URL}/user/load"
        params = {"token": self._token}

        try:
            async with session.get(url, params=params) as resp:
                data = await resp.json()

                if not data.get("success"):
                    msg = data.get("message", {}).get(
                        "description", "Failed to load devices"
                    )
                    # Check if it's an auth issue
                    if data.get("message", {}).get("id") in (4010, 4011, 4012):
                        raise KolorsKultAuthError(msg)
                    raise KolorsKultApiError(msg)

                return data["data"]

        except aiohttp.ClientError as err:
            raise KolorsKultApiError(f"Connection error: {err}") from err

    async def update_device_settings(
        self, device_id: str, settings: dict[str, Any]
    ) -> bool:
        """Update a device's settings.

        POST /app/1.3/device/updateSettings
        Body: {"token": "...", "devices": [{"device_id": "...", "settings": {...}}]}
        """
        if not self._token:
            raise KolorsKultAuthError("Not authenticated")

        session = await self._get_session()
        url = f"{API_BASE_URL}/device/updateSettings"
        payload = {
            "token": self._token,
            "devices": [{"device_id": device_id, "settings": settings}],
        }

        try:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()

                if not data.get("success"):
                    msg = data.get("message", {}).get(
                        "description", "Failed to update device"
                    )
                    if data.get("message", {}).get("id") in (4010, 4011, 4012):
                        raise KolorsKultAuthError(msg)
                    raise KolorsKultApiError(msg)

                return True

        except aiohttp.ClientError as err:
            raise KolorsKultApiError(f"Connection error: {err}") from err

    async def set_button_state(self, device_id: str, state: bool) -> bool:
        """Turn a button (switch) on or off."""
        settings = {
            "speed": 0.0,
            "status": state,
            "child_lock": False,
            "steps": 0,
            "index": 0,
            "state": 0,
        }
        return await self.update_device_settings(device_id, settings)

    async def set_dimmer_state(
        self, device_id: str, *, on: bool, speed: float = 0.0, steps: int = 8
    ) -> bool:
        """Set fan regulator / 8-step dimmer state.

        Args:
            device_id: The device ID.
            on: Whether the dimmer is on or off.
            speed: Speed percentage (0, 12.5, 25, 37.5, ..., 100).
            steps: Number of steps (default 8).
        """
        settings = {
            "speed": speed if on else 0.0,
            "status": on,
            "child_lock": False,
            "steps": steps,
            "index": 0,
            "state": 0,
        }
        return await self.update_device_settings(device_id, settings)

    async def close(self) -> None:
        """Close the API session."""
        if self._session and not self._session.closed:
            await self._session.close()
