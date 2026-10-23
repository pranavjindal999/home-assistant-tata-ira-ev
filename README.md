# Tata iRA.ev

Home Assistant sensors for a Tata EV that uses the iRA.ev app:

- Battery percentage
- Charging on or off
- Minutes remaining while the car is charging

Readings refresh about every 5 minutes. This is unofficial and is not part of Tata Motors.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=pranavjindal999&repository=tata-ira-ev&category=integration)

## Install

1. Click the button above. Home Assistant opens the repository in Marketplace, or in HACS on older versions. Install it.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration**, and choose **Tata iRA.ev**.

## Setup values

The form asks for three values from the phone's own iRA.ev session:

| Field | Where it appears |
| --- | --- |
| Vehicle ID | `vehicleId` header on a vehicle-health request |
| API key | `x-api-key` header on that same request |
| Refresh token | `refreshToken` in the body of a refresh-token request |

Those requests go to `evcx.api.tatamotors`. If you sign out of iRA.ev or change the account password, paste a new refresh token.

## Entities

| Entity | Meaning |
| --- | --- |
| `sensor.tata_ira_ev_battery` | Battery percentage |
| `binary_sensor.tata_ira_ev_charging` | On while the car is charging |
| `sensor.tata_ira_ev_charge_time_remaining` | Minutes left, only while charging |
