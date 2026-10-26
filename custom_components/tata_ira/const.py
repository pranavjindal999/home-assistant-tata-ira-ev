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
# Full reading while the live channel is connected. Live messages fill the gap.
LIVE_RECONCILE_INTERVAL = timedelta(minutes=10)
# While the command link is awake, confirm it before the car can go to sleep.
KEEP_CONNECTED_INTERVAL = timedelta(minutes=2)
# After startup, or after the car reports it is asleep, try again quickly.
RECONNECT_INTERVAL = timedelta(seconds=15)

API_HOST = "https://evcx.api.tatamotors"
# Live last-known-state routes live on this host, not on API_HOST.
LKS_HOST = "https://customer.api.ev.tatamotors.io"
# That host rejects other clients. The app's Flutter HTTP client sends this.
LKS_USER_AGENT = "Dart/3.5 (dart:io)"
REFRESH_PATH = "/mobile/customer/api/v1/refresh-token"
CHECK_PHONE_PATH = "/mobile/customer/api/v1/check-phonenumber"
VERIFY_OTP_PATH = "/mobile/customer/api/v1/verify-phone-otp"
ACCESS_TOKEN_PATH = "/mobile/customer/api/v1/access-token"
PROFILE_PATH = "/mobile/cvp/api/v1/ev/profiles/get-profile"
HEALTH_PATH = "/mobile/cvp/api/v1/ev/vehicle-health"
STATE_PATH = "/mobile/cvp/api/v1/ev/vehicle-state"
COMMAND_LOG_PATH = "/mobile/cvp/api/v1/ev/command-log"
COMMAND_PATH = "/mobile/cvp/api/v1/ev/vehicle-command"
COMMAND_STATUS_PATH = "/mobile/cvp/api/v1/ev/vehicle-command-status"
WAKE_PATH = "/mobile/cvp/api/v1/ev/wake-up-device"
DEVICE_STATUS_PATH = "/mobile/cvp/api/v1/ev/check-device-status"
ECDH_PATH = "/mobile/customer/api/v1/security/ecdh-key-exchange"
LKS_TEMPLATE_PATH = "/v1/vehicles/{vehicle_id}/lks/template"
LKS_ACTIVATE_PATH = "/v1/vehicles/{vehicle_id}/lks/template/activate"

# Same client identity the official Android app sends. The installed app is 26.9.1.
CLIENT_ID = "TMLEV-ANDROID-APP"
NIO_CLIENT_ID = "TMLEV-NIO-ANDROID-APP"
CLIENT_SECRET = "ef167580-88df-4f6a-847d-039fa3c7e6fa"
APP_API_KEY = "36pdpewgXQ5N3eZTxt5cF70v34Re2tNB4hNVc5K2"
APP_VERSION = "26.9.1"
OTP_REDIRECT_URL = "https://prod-ev.tatamotors.com/"
