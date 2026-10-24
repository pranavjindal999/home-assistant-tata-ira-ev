"""Config flow for a Tata iRA.ev vehicle."""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_REAUTH, ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from .api import (
    IraAuthError,
    IraClient,
    IraConnectionError,
    IraError,
    async_send_otp,
    async_sign_in,
)
from .const import (
    APP_API_KEY,
    CONF_API_KEY,
    CONF_COUNTRY_CODE,
    CONF_OTP,
    CONF_PHONE,
    CONF_REFRESH_TOKEN,
    CONF_VEHICLE_ID,
    DOMAIN,
)


def _digits(value: str) -> str:
    return "".join(character for character in value if character.isdigit())


def _phone_parts(user_input: dict) -> tuple[str, str]:
    country = _digits(user_input.get(CONF_COUNTRY_CODE, "")) or "91"
    phone = _digits(user_input.get(CONF_PHONE, ""))
    if phone.startswith(country) and len(phone) > 10:
        phone = phone[len(country) :]
    if phone.startswith("0"):
        phone = phone.lstrip("0")
    return country, phone


class TataIraConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ask for the phone number and sign-in code, then connect the car."""

    VERSION = 1

    def __init__(self) -> None:
        """Keep the sign-in details until the code is accepted."""
        self._country_code = "91"
        self._phone = ""
        self._ref_id = ""
        self._user_type = "existing"
        self._refresh_token = ""
        self._vehicle_ids: list[str] = []

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        """Ask for the mobile number and text a sign-in code."""
        errors: dict[str, str] = {}
        if user_input is not None:
            country, phone = _phone_parts(user_input)
            if len(phone) < 8:
                errors["base"] = "invalid_phone"
            else:
                self._country_code = country
                self._phone = phone
                try:
                    self._ref_id, self._user_type = await async_send_otp(
                        async_get_clientsession(self.hass), country, phone
                    )
                except IraAuthError:
                    errors["base"] = "otp_failed"
                except IraConnectionError:
                    errors["base"] = "cannot_connect"
                except IraError:
                    errors["base"] = "unknown"
                else:
                    return await self.async_step_otp()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_COUNTRY_CODE, default=self._country_code): str,
                    vol.Required(CONF_PHONE, default=self._phone): str,
                }
            ),
            errors=errors,
        )

    async def async_step_otp(self, user_input: dict | None = None) -> ConfigFlowResult:
        """Ask for the texted code and connect the car."""
        errors: dict[str, str] = {}
        if user_input is not None:
            otp = _digits(user_input.get(CONF_OTP, ""))
            if len(otp) < 4:
                errors["base"] = "invalid_otp"
            else:
                try:
                    refresh_token, vehicle_ids = await async_sign_in(
                        async_get_clientsession(self.hass),
                        self._country_code,
                        self._phone,
                        otp,
                        self._ref_id,
                        self._user_type,
                    )
                except IraAuthError as err:
                    errors["base"] = (
                        "invalid_otp" if err.code == "SSO-1138" else "invalid_auth"
                    )
                except IraConnectionError:
                    errors["base"] = "cannot_connect"
                except IraError:
                    errors["base"] = "unknown"
                else:
                    if not vehicle_ids:
                        errors["base"] = "no_vehicle"
                    else:
                        self._refresh_token = refresh_token
                        self._vehicle_ids = vehicle_ids
                        if len(vehicle_ids) == 1:
                            return await self._async_finish(vehicle_ids[0])
                        return await self.async_step_vehicle()
        return self.async_show_form(
            step_id="otp",
            data_schema=vol.Schema({vol.Required(CONF_OTP): str}),
            description_placeholders={"phone": self._phone},
            errors=errors,
        )

    async def async_step_vehicle(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Ask which car to connect when the account has more than one."""
        if user_input is not None:
            return await self._async_finish(user_input[CONF_VEHICLE_ID])
        return self.async_show_form(
            step_id="vehicle",
            data_schema=vol.Schema(
                {vol.Required(CONF_VEHICLE_ID): vol.In(self._vehicle_ids)}
            ),
        )

    async def async_step_reauth(
        self, entry_data: dict | None = None
    ) -> ConfigFlowResult:
        """Sign in again when the saved session is rejected."""
        return await self.async_step_user()

    async def _async_finish(self, vehicle_id: str) -> ConfigFlowResult:
        data = {
            CONF_VEHICLE_ID: vehicle_id,
            CONF_API_KEY: APP_API_KEY,
            CONF_REFRESH_TOKEN: self._refresh_token,
        }
        error = await self._async_validate(data)
        if error:
            return self.async_show_form(
                step_id="otp",
                data_schema=vol.Schema({vol.Required(CONF_OTP): str}),
                description_placeholders={"phone": self._phone},
                errors={"base": error},
            )
        await self.async_set_unique_id(vehicle_id)
        if self.source == SOURCE_REAUTH:
            self._abort_if_unique_id_mismatch(reason="wrong_account")
            return self.async_update_reload_and_abort(
                self._get_reauth_entry(),
                data=data,
            )
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title="Tata iRA.ev", data=data)

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
