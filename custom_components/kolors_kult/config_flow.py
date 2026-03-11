"""Config flow for Kolors Kult integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .api import KolorsKultApi, KolorsKultApiError, KolorsKultAuthError
from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class KolorsKultConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kolors Kult."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step — email and password."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api = KolorsKultApi(
                email=user_input[CONF_EMAIL],
                password=user_input[CONF_PASSWORD],
            )

            try:
                user_data = await api.authenticate()
            except KolorsKultAuthError:
                errors["base"] = "invalid_auth"
            except KolorsKultApiError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception during login")
                errors["base"] = "unknown"
            else:
                await api.close()

                # Use email as unique ID to prevent duplicate entries
                await self.async_set_unique_id(user_input[CONF_EMAIL])
                self._abort_if_unique_id_configured()

                first_name = user_data.get("first_name", "")
                last_name = user_data.get("last_name", "")
                title = f"Kolors Kult ({first_name} {last_name})".strip()

                return self.async_create_entry(title=title, data=user_input)
            finally:
                await api.close()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
