# Tata iRA.ev

Home Assistant sensors and controls for a Tata EV that uses the iRA.ev app:

- Battery percentage
- Charging on or off
- Minutes remaining while the car is charging
- Cabin air conditioning: turn it on for 0 to 30 minutes, or turn it off

Readings refresh every 30 seconds. Press Refresh to update immediately. This is unofficial and is not part of Tata Motors.

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
| `switch.tata_ira_ev_air_conditioning` | On starts the air conditioner. Off stops it |
| `number.tata_ira_ev_air_conditioning_duration` | How long the next start runs, from 0 to 30 minutes |
| `button.tata_ira_ev_refresh` | Read battery, charging, and air conditioning now |

Set the duration, then turn the switch on. The car runs the air conditioner for that many minutes at 25°. Turning the switch off stops it. The switch follows the car's reported air-conditioning state, which can take a few minutes to change.
