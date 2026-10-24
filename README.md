# Tata iRA.ev

Home Assistant sensors and controls for a Tata EV that uses the iRA.ev app:

- Battery percentage
- Charging on or off
- Minutes remaining while the car is charging
- Cabin air conditioning: turn it on for 0 to 30 minutes, or turn it off
- Approach lights, headlights, and hazard lights
- Horn
- Remote start, for the same duration as the air conditioner
- Lock or unlock the car, and whether it is locked

Readings refresh every 30 seconds. Press Refresh to update immediately. Home Assistant also keeps the car's command link awake, the same link the phone app has to open again after it has been left for a few hours. A command can run without waiting for that connection. This is unofficial and is not part of Tata Motors.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=pranavjindal999&repository=tata-ira-ev&category=integration)

## Install

1. Click the button above. Home Assistant opens the repository in Marketplace, or in HACS on older versions. Install it.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration**, and choose **Tata iRA.ev**.

## Setup

The form asks for the mobile number on the iRA.ev account, then the code sent by text. The car and session are picked up from that sign-in. If the account has more than one car, choose which one to add.

If iRA.ev later rejects the saved session, Home Assistant asks for the mobile number and a new code.

## Entities

| Entity | Meaning |
| --- | --- |
| `sensor.tata_ira_ev_battery` | Battery percentage |
| `binary_sensor.tata_ira_ev_charging` | On while the car is charging |
| `binary_sensor.tata_ira_ev_connected` | On while the command link is awake |
| `sensor.tata_ira_ev_charge_time_remaining` | Minutes left, only while charging |
| `switch.tata_ira_ev_air_conditioning` | On starts the air conditioner. Off stops it |
| `number.tata_ira_ev_air_conditioning_duration` | How long the next air-conditioning or remote start runs, from 0 to 30 minutes |
| `switch.tata_ira_ev_approach_lights` | Approach lights |
| `switch.tata_ira_ev_headlights` | Headlights |
| `switch.tata_ira_ev_hazard_lights` | Hazard lights |
| `switch.tata_ira_ev_remote_start` | On starts the car. Off stops it |
| `button.tata_ira_ev_horn` | Sound the horn |
| `button.tata_ira_ev_refresh` | Read the car now |
| `lock.tata_ira_ev_lock` | Locked or unlocked. Lock and unlock the car |

Set the duration, then turn the switch on. The car runs the air conditioner for that many minutes at 25°. Turning the switch off stops it. The switch follows the car's reported air-conditioning state, which can take a few minutes to change.
