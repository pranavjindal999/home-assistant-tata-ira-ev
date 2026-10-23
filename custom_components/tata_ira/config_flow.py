"""Config flow for a Tata iRA.ev vehicle."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IraAuthError, IraClient, IraConnectionError, IraError
from .const import CONF_API_KEY, CONF_REFRESH_TOKEN, CONF_VEHICLE_ID, DOMAIN


def _schema(user_input: dict | None) -> vol.Schema:
    current = user_input or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_VEHICLE_ID, default=current.get(CONF_VEHICLE_ID, "")
            ): str,
            vol.Required(CONF_API_KEY): str,
            vol.Required(CONF_REFRESH_TOKEN): str,
        }
    )


class TataIraConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ask for the car session, then confirm battery and charging can be read."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        """Collect the session values and read the car once."""
        errors: dict[str, str] = {}
        if user_input is not None:
            vehicle_id = user_input[CONF_VEHICLE_ID].strip()
            user_input = {
                CONF_VEHICLE_ID: vehicle_id,
                CONF_API_KEY: user_input[CONF_API_KEY].strip(),
                CONF_REFRESH_TOKEN: user_input[CONF_REFRESH_TOKEN].strip(),
            }
            await self.async_set_unique_id(vehicle_id)
            self._abort_if_unique_id_configured()
            error = await self._async_validate(user_input)
            if error:
                errors["base"] = error
            else:
                return self.async_create_entry(title="Tata iRA.ev", data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=_schema(user_input),
            errors=errors,
        )

    async def _async_validate(self, user_input: dict) -> str | None:
        client = IraClient(
            async_get_clientsession(self.hass),
            user_input[CONF_REFRESH_TOKEN],
            user_input[CONF_VEHICLE_ID],
            user_input[CONF_API_KEY],
        )
        try:
            await client.async_vehicle_status()
        except IraAuthError:
            return "invalid_auth"
        except IraConnectionError:
            return "cannot_connect"
        except IraError:
            return "unknown"
        return None
