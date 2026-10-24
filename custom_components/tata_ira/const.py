"""Constants for the Tata iRA.ev integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "tata_ira"

CONF_REFRESH_TOKEN = "refresh_token"
CONF_VEHICLE_ID = "vehicle_id"
CONF_API_KEY = "api_key"
CONF_COUNTRY_CODE = "country_code"
CONF_PHONE = "phone"
CONF_OTP = "otp"

POLL_INTERVAL = timedelta(seconds=30)

API_HOST = "https://evcx.api.tatamotors"
REFRESH_PATH = "/mobile/customer/api/v1/refresh-token"
CHECK_PHONE_PATH = "/mobile/customer/api/v1/check-phonenumber"
VERIFY_OTP_PATH = "/mobile/customer/api/v1/verify-phone-otp"
ACCESS_TOKEN_PATH = "/mobile/customer/api/v1/access-token"
PROFILE_PATH = "/mobile/cvp/api/v1/ev/profiles/get-profile"
HEALTH_PATH = "/mobile/cvp/api/v1/ev/vehicle-health"
STATE_PATH = "/mobile/cvp/api/v1/ev/vehicle-state"
COMMAND_LOG_PATH = "/mobile/cvp/api/v1/ev/command-log"
COMMAND_PATH = "/mobile/cvp/api/v1/ev/vehicle-command"

# Same client identity the official Android app sends. The installed app is 26.9.1.
CLIENT_ID = "TMLEV-ANDROID-APP"
CLIENT_SECRET = "ef167580-88df-4f6a-847d-039fa3c7e6fa"
APP_API_KEY = "36pdpewgXQ5N3eZTxt5cF70v34Re2tNB4hNVc5K2"
APP_VERSION = "26.9.1"
OTP_REDIRECT_URL = "https://prod-ev.tatamotors.com/"
