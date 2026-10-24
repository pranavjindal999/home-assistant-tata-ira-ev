"""Read battery and charging status from the iRA.ev service."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime
from typing import Any
from uuid import uuid4

import aiohttp

from .const import (
    ACCESS_TOKEN_PATH,
    API_HOST,
    APP_API_KEY,
    APP_VERSION,
    CHECK_PHONE_PATH,
    CLIENT_ID,
    CLIENT_SECRET,
    COMMAND_LOG_PATH,
    COMMAND_PATH,
    COMMAND_STATUS_PATH,
    DEVICE_STATUS_PATH,
    WAKE_PATH,
    HEALTH_PATH,
    PROFILE_PATH,
    REFRESH_PATH,
    STATE_PATH,
    VERIFY_OTP_PATH,
)
from .parser import (
    VehicleStatus,
    ac_command_body,
    command_log_body,
    empty_command_body,
    timed_command_body,
    command_progress,
    lock_command_body,
    parse_command_log,
    parse_command_status,
    parse_device_awake,
    otp_verify_body,
    parse_air_conditioning,
    parse_auth_code,
    parse_code_verifier,
    parse_login_tokens,
    parse_user_type,
    parse_ref_id,
    parse_refresh_tokens,
    parse_vehicle_health,
    parse_vehicle_ids,
    service_error,
)

_LOGGER = logging.getLogger(__name__)


class IraError(Exception):
    """The iRA.ev service could not be read."""


class IraAuthError(IraError):
    """The saved session was rejected."""

    def __init__(self, message: str, code: str | None = None) -> None:
        """Store the service error code when one was returned."""
        super().__init__(message)
        self.code = code


class IraConnectionError(IraError):
    """The iRA.ev service could not be reached."""


class IraClient:
    """Session client for one Tata vehicle."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        refresh_token: str,
        vehicle_id: str,
        api_key: str,
    ) -> None:
        """Store the session values Home Assistant collected."""
        self._session = session
        self.refresh_token = refresh_token
        self._vehicle_id = vehicle_id
        self._api_key = api_key

    async def async_vehicle_status(self) -> tuple[VehicleStatus, str | None]:
        """Refresh the session and return battery and charging status.

        The second value is a replacement refresh token when the service rotates it.
        """
        access_token, rotated = await self._async_refresh()
        status = await self._async_health(access_token)
        try:
            ac_on = await self._async_air_conditioning(access_token)
        except IraError as err:
            _LOGGER.debug("Air conditioning state was not available: %s", err)
        else:
            status = replace(status, ac_on=ac_on)
        return status, rotated

    async def async_set_air_conditioning(
        self, on: bool, minutes: int
    ) -> str | None:
        """Start the air conditioner for a number of minutes, or stop it."""
        matches, rotated = await self._async_air_matches(on)
        if matches:
            return rotated
        command, _body = ac_command_body(on, minutes, "")
        return await self._async_vehicle_command(
            command,
            lambda trace_id: ac_command_body(on, minutes, trace_id)[1],
            lambda: self._async_air_matches(on),
        )

    async def async_set_switch(
        self,
        on: bool,
        on_command: str,
        off_command: str,
        field: str,
    ) -> str | None:
        """Turn one reported car feature on or off."""

        async def matches() -> tuple[bool, str | None]:
            return await self._async_health_flag(field, on)

        current, rotated = await matches()
        if current:
            return rotated
        command = on_command if on else off_command
        return await self._async_vehicle_command(
            command, empty_command_body, matches
        )

    async def async_set_engine(self, on: bool, minutes: int) -> str | None:
        """Start the car for a number of minutes, or stop it."""

        async def matches() -> tuple[bool, str | None]:
            return await self._async_health_flag("engine_on", on)

        current, rotated = await matches()
        if current:
            return rotated
        if on:
            return await self._async_vehicle_command(
                "RemoteEngineStartCommand",
                lambda trace_id: timed_command_body(minutes, trace_id),
                matches,
            )
        return await self._async_vehicle_command(
            "RemoteEngineStopCommand", empty_command_body, matches
        )

    async def async_honk(self) -> str | None:
        """Sound the horn once."""
        return await self._async_vehicle_command(
            "RemoteHonkCommand",
            empty_command_body,
            self._async_not_already,
        )

    async def async_set_locked(self, locked: bool) -> str | None:
        """Lock or unlock the car."""
        matches, rotated = await self._async_lock_matches(locked)
        if matches:
            return rotated
        command, _body = lock_command_body(locked, "")
        return await self._async_vehicle_command(
            command,
            lambda trace_id: lock_command_body(locked, trace_id)[1],
            lambda: self._async_lock_matches(locked),
        )

    async def _async_vehicle_command(
        self,
        command: str,
        body_for: Callable[[str], dict[str, Any]],
        already: Callable[[], Any],
    ) -> str | None:
        """Log the command, wake the car when it is asleep, then send it.

        The fingerprint prompt in the app is local and is not part of this request.
        A temporary rejection is retried. If the car already has the requested
        state, that state is kept instead of reporting the rejection.
        """
        last_error: IraError | None = None
        rotated: str | None = None
        for attempt in range(3):
            try:
                rotated_now = await self._async_send_command(command, body_for)
            except (IraAuthError, IraConnectionError):
                raise
            except IraError as err:
                last_error = err
                if not _temporary_command_error(err) or attempt == 2:
                    break
                await asyncio.sleep(4)
                continue
            if rotated_now:
                rotated = rotated_now
            return rotated
        if last_error is not None and _temporary_command_error(last_error):
            matches, rotated_now = await already()
            if rotated_now:
                rotated = rotated_now
            if matches:
                return rotated
        if last_error is not None:
            raise last_error
        return rotated

    async def _async_send_command(
        self, command: str, body_for: Callable[[str], dict[str, Any]]
    ) -> str | None:
        access_token, rotated = await self._async_refresh()
        headers = {
            **self._vehicle_headers(access_token),
            "Accept": "application/json",
            "Cache-Control": "no-cache, no-store",
            "X-Request-ID": str(uuid4()),
        }
        logged = await self._async_request(
            "POST",
            COMMAND_LOG_PATH,
            json_body=command_log_body(
                self._vehicle_id,
                command,
                datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            ),
            headers=headers,
        )
        self._raise_service_error(logged)
        trace_id, connected = parse_command_log(logged)
        if not trace_id:
            raise IraError("iRA.ev did not return a command id")
        if connected is False:
            await self._async_wake(access_token, trace_id)
        result = await self._async_request(
            "POST",
            COMMAND_PATH,
            json_body=body_for(trace_id),
            headers={
                **headers,
                "command-name": command,
                "X-Request-ID": str(uuid4()),
            },
        )
        self._raise_service_error(result)
        await self._async_wait_for_command(access_token, result)
        return rotated

    async def _async_wake(self, access_token: str, trace_id: str) -> None:
        """Wake the command unit, then wait until it reports it is awake."""
        headers = {
            **self._vehicle_headers(access_token),
            "Accept": "application/json",
            "Cache-Control": "no-cache, no-store",
            "commandTraceId": trace_id,
            "X-Request-ID": str(uuid4()),
        }
        try:
            await self._async_request("GET", WAKE_PATH, headers=headers)
        except IraError:
            _LOGGER.debug("Wake request was not accepted")
        for _ in range(4):
            await asyncio.sleep(2)
            try:
                status = await self._async_request(
                    "GET",
                    DEVICE_STATUS_PATH,
                    headers={**headers, "X-Request-ID": str(uuid4())},
                )
            except IraError:
                continue
            if parse_device_awake(status) is True:
                return
        raise IraError("The car is not connected")

    async def _async_wait_for_command(
        self, access_token: str, result: dict[str, Any]
    ) -> None:
        status, correlation = parse_command_status(result)
        if command_progress(status) == "failed":
            raise IraError("The car did not accept the command")
        if command_progress(status) != "wait" or not correlation:
            return
        headers = {
            **self._vehicle_headers(access_token),
            "Accept": "application/json",
            "Cache-Control": "no-cache, no-store",
            "correlationId": correlation,
        }
        for _ in range(6):
            await asyncio.sleep(3)
            polled = await self._async_request(
                "GET",
                COMMAND_STATUS_PATH,
                headers={**headers, "X-Request-ID": str(uuid4())},
            )
            self._raise_service_error(polled)
            polled_status, _correlation = parse_command_status(polled)
            progress = command_progress(polled_status)
            if progress == "failed":
                raise IraError("The car did not accept the command")
            if progress == "done":
                return
        raise IraError("The car is still applying that command")

    async def _async_air_matches(self, on: bool) -> tuple[bool, str | None]:
        try:
            access_token, rotated = await self._async_refresh()
            return await self._async_air_conditioning(access_token) is on, rotated
        except IraError:
            return False, None

    async def _async_health_flag(
        self, field: str, expected: bool
    ) -> tuple[bool, str | None]:
        try:
            access_token, rotated = await self._async_refresh()
            status = await self._async_health(access_token)
        except IraError:
            return False, None
        return getattr(status, field) is expected, rotated

    async def _async_not_already(self) -> tuple[bool, str | None]:
        return False, None

    async def _async_lock_matches(self, locked: bool) -> tuple[bool, str | None]:
        try:
            access_token, rotated = await self._async_refresh()
            return (await self._async_health(access_token)).locked is locked, rotated
        except IraError:
            return False, None

    def _raise_service_error(self, payload: dict[str, Any]) -> None:
        message, _code = service_error(payload)
        if message:
            raise IraError(message)

    async def _async_refresh(self) -> tuple[str, str | None]:
        body = {"refreshToken": self.refresh_token}
        payload = await self._async_request(
            "POST",
            REFRESH_PATH,
            json_body=body,
            headers={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "App-Version": APP_VERSION,
                "x-api-key": self._api_key,
            },
        )
        access_token, rotated = parse_refresh_tokens(payload)
        if not access_token:
            raise IraAuthError("The session refresh did not return an access token")
        if rotated and rotated != self.refresh_token:
            self.refresh_token = rotated
            return access_token, rotated
        return access_token, None

    async def _async_health(self, access_token: str) -> VehicleStatus:
        payload = await self._async_request(
            "GET",
            HEALTH_PATH,
            headers=self._vehicle_headers(access_token),
        )
        return parse_vehicle_health(payload)

    async def _async_air_conditioning(self, access_token: str) -> bool | None:
        payload = await self._async_request(
            "GET",
            STATE_PATH,
            headers=self._vehicle_headers(access_token),
        )
        return parse_air_conditioning(payload)

    def _vehicle_headers(self, access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "client_id": CLIENT_ID,
            "vehicleId": self._vehicle_id,
            "x-api-key": self._api_key,
            "App-Version": APP_VERSION,
        }

    async def _async_request(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            async with self._session.request(
                method,
                f"{API_HOST}{path}",
                headers=headers,
                json=json_body,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as response:
                if response.status in (401, 403):
                    raise IraAuthError("iRA.ev rejected this session")
                if response.status >= 400:
                    raise IraError(f"iRA.ev returned HTTP {response.status}")
                payload = await response.json(content_type=None)
        except (IraError, IraAuthError):
            raise
        except (aiohttp.ClientError, TimeoutError) as err:
            raise IraConnectionError("Cannot reach the iRA.ev service") from err
        if not isinstance(payload, dict):
            raise IraError("iRA.ev returned an unexpected response")
        return payload


def _temporary_command_error(err: IraError) -> bool:
    text = str(err).lower()
    return "not connected" in text or "temporarily unavailable" in text


def _login_headers(access_token: str | None = None) -> dict[str, str]:
    headers = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "App-Version": APP_VERSION,
        "x-api-key": APP_API_KEY,
        "Accept": "application/json",
    }
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers


async def async_send_otp(
    session: aiohttp.ClientSession, country_code: str, phone: str
) -> tuple[str, str]:
    """Text a sign-in code and return its reference id and account type."""
    payload = await _async_login_request(
        session,
        "POST",
        CHECK_PHONE_PATH,
        json_body={"countryCode": country_code, "phone": phone, "sendOtp": True},
    )
    ref_id = parse_ref_id(payload)
    if not ref_id:
        raise IraAuthError("iRA.ev did not send a verification code")
    return ref_id, parse_user_type(payload)


async def async_sign_in(
    session: aiohttp.ClientSession,
    country_code: str,
    phone: str,
    otp: str,
    ref_id: str,
    user_type: str,
) -> tuple[str, list[str]]:
    """Exchange the sign-in code for a refresh token and the account's cars."""
    verified = await _async_login_request(
        session,
        "POST",
        VERIFY_OTP_PATH,
        json_body=otp_verify_body(country_code, phone, otp, ref_id),
    )
    verifier = parse_code_verifier(verified)
    auth_code = parse_auth_code(verified)
    if not verifier or not auth_code:
        raise IraAuthError("That code was not accepted")
    tokens = await _async_login_request(
        session,
        "POST",
        ACCESS_TOKEN_PATH,
        json_body={"codeVerifier": verifier},
        headers={
            **_login_headers(),
            "authCode": auth_code,
            "userType": user_type,
            "convertToLoyal": "false",
            "X-Request-ID": str(uuid4()),
        },
    )
    access_token, refresh_token = parse_login_tokens(tokens)
    if not access_token or not refresh_token:
        raise IraAuthError("iRA.ev did not return a session")
    profile = await _async_login_request(
        session,
        "GET",
        PROFILE_PATH,
        headers=_login_headers(access_token),
    )
    return refresh_token, parse_vehicle_ids(profile)


async def _async_login_request(
    session: aiohttp.ClientSession,
    method: str,
    path: str,
    json_body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    try:
        async with session.request(
            method,
            f"{API_HOST}{path}",
            headers=headers or _login_headers(),
            json=json_body,
            timeout=aiohttp.ClientTimeout(total=20),
        ) as response:
            try:
                payload = await response.json(content_type=None)
            except (aiohttp.ContentTypeError, ValueError):
                payload = None
            if not isinstance(payload, dict):
                if response.status in (401, 403, 400):
                    raise IraAuthError(f"iRA.ev returned HTTP {response.status}")
                if response.status >= 400:
                    raise IraError(f"iRA.ev returned HTTP {response.status}")
                raise IraError("iRA.ev returned an unexpected response")
            message, code = service_error(payload)
            if response.status in (401, 403, 400) or message:
                raise IraAuthError(
                    message or f"iRA.ev returned HTTP {response.status}",
                    code=code,
                )
            if response.status >= 400:
                raise IraError(f"iRA.ev returned HTTP {response.status}")
            return payload
    except (IraError, IraAuthError):
        raise
    except (aiohttp.ClientError, TimeoutError) as err:
        raise IraConnectionError("Cannot reach the iRA.ev service") from err
