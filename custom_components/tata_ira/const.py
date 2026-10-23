"""Constants for the Tata iRA.ev integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "tata_ira"

CONF_REFRESH_TOKEN = "refresh_token"
CONF_VEHICLE_ID = "vehicle_id"
CONF_API_KEY = "api_key"

POLL_INTERVAL = timedelta(minutes=5)

API_HOST = "https://evcx.api.tatamotors"
REFRESH_PATH = "/mobile/customer/api/v1/refresh-token"
HEALTH_PATH = "/mobile/cvp/api/v1/ev/vehicle-health"

# Same client identity the official Android app sends. The installed app is 26.9.1.
CLIENT_ID = "TMLEV-ANDROID-APP"
CLIENT_SECRET = "ef167580-88df-4f6a-847d-039fa3c7e6fa"
APP_VERSION = "26.9.1"
