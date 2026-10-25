# Tata iRA.ev

Home Assistant custom integration for a Tata Motors electric vehicle that uses the [iRA.ev](https://www.tatamotors.com/) app. It reads the car every 30 seconds and sends the same remote commands the app sends: air conditioning, lights, horn, and lock.

The **Tata iRA.ev** dashboard card puts the battery, the controls, and the sensors on one card.

This project is unofficial and is not part of Tata Motors.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=pranavjindal999&repository=home-assistant-tata-ira-ev&category=integration)
[![GitHub release](https://img.shields.io/github/v/release/pranavjindal999/home-assistant-tata-ira-ev)](https://github.com/pranavjindal999/home-assistant-tata-ira-ev/releases)

Requires Home Assistant 2024.8.0 or newer.

## Features

### Battery and charging

- **Battery** is the high-voltage battery percentage.
- **Charging** is on while the car is charging.
- **Charge time remaining** is the minutes left until full. It only has a value while the car is charging.

Home Assistant reads these every 30 seconds. **Refresh** reads them immediately.

### Tyre pressure

The same four pressures the iRA.ev app shows. The car reports them in psi, and Home Assistant can display another pressure unit from the entity settings:

- **Front left tyre**
- **Front right tyre**
- **Back left tyre**
- **Back right tyre**

**Tyre pressure** is on when the app would mark any of those tyres as low. A blank or zero reading is left empty, which is how the app shows a tyre it is not reporting.

### Car details

These come from the same status the app already downloads. Several of them are not shown as numbers in the app.

- **Range** is the remaining distance.
- **Odometer** is the total distance.
- **12V battery** is the auxiliary battery voltage. **12V battery low** is on when the car reports that battery as low.
- **Service due** is the days until the next service. **Service distance** is the kilometres until that service.
- **Speed** is the speed from the latest status.
- **Charger connected** is on when a charger is plugged in, including before charging starts.
- **Warning** is on when the car reports a fault lamp, such as the check-engine, ABS, airbag, high battery temperature, motor, or transmission warning.
- **Front left door**, **Front right door**, **Rear left door**, **Rear right door**, **Bonnet**, and **Tailgate** are on while that opening is open.
- **Location** is a map of where the car last reported it is.
- **Ignition** is on while the car is switched on.
- **Key in car** is on when the key is inside the car.
- **High beam** and **Low beam** are the beam telltales. They are separate from the **Headlights** switch, which controls the position lamps.

### Air conditioning

The air conditioner uses the same fixed cabin temperature as the iRA.ev app, 25°.

**Air conditioning duration** is how long the next start runs, from 0 to 30 minutes. The default is 10. Home Assistant stores this number. It is sent only when you turn the air conditioner on.

**Air conditioning** turns the cabin air conditioner on or off:

- If it is off, turning the switch on starts it for the saved duration.
- If it is on, turning the switch off stops it.

### Lights

Each light switch shows the state the car reports, and sends the matching command from the app’s lights screen.

- **Approach lights** are the approach lamps.
- **Headlights** are the position lamps on that screen. This is the headlight control in the app, separate from the high-beam and low-beam telltales.
- **Hazard lights** are the hazard lamps.

### Horn

**Horn** sounds the horn once. It is a button, so it has no on or off state.

### Lock

**Lock** shows whether the car is locked, and locks or unlocks it.

### Command link

**Connected** is on while the car’s command link is awake. Home Assistant opens that link when it starts and checks it every couple of minutes, so a command hours later does not have to wake the car first.

A rate limit, a short outage, or a slow wake does not turn Connected off. The car’s link falls asleep after a few minutes, and Home Assistant wakes it again before that shows up as disconnected. Connected turns off only when the car still does not answer after that wake.

### While a command runs

A switch, the lock, or the horn stays on its current state and shows loading until iRA.ev reports that the command has finished. Accepted or queued is not finished. The control changes after the server reports success.

## Install

### HACS

1. Click the button at the top. Home Assistant opens this repository in Marketplace, or in HACS on older versions. Install **Tata iRA.ev**.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration** and choose **Tata iRA.ev**.

To update later, update Tata iRA.ev in HACS and restart Home Assistant.

### Manual

1. Copy `custom_components/tata_ira` into `config/custom_components/tata_ira`.
2. Restart Home Assistant.
3. Add the **Tata iRA.ev** integration as above.

## Setup

The form asks for the country code and the mobile number on the iRA.ev account. iRA.ev texts a code. Enter that code. The car and the session are taken from that sign-in. If the account has more than one car, choose which one to add.

The mobile number and the code are not stored. Home Assistant keeps the session for that car. If iRA.ev later rejects the session, Home Assistant asks for the mobile number and a new code.

Each car can be added once.

## Dashboard

Update to the latest release, restart Home Assistant, and reload the browser tab. Then edit a dashboard, add a card, and choose **Tata iRA.ev**. The card finds the car. You do not add the lock, the lights, or the sensors one by one. On a phone it stays in one column. On a wider dashboard the controls, readings, and the map sit side by side.

The same card in YAML is:

```yaml
type: custom:tata-ira-card
```

With more than one car, pick the car on the card, or set any entity from that car:

```yaml
type: custom:tata-ira-card
entity: sensor.tata_ira_ev_battery
```

## Entities

Default entity IDs use the device name Tata iRA.ev. If you rename the device, Home Assistant changes the IDs.

| Entity | What it does |
| --- | --- |
| `sensor.tata_ira_ev_battery` | Battery percentage |
| `binary_sensor.tata_ira_ev_charging` | On while the car is charging |
| `sensor.tata_ira_ev_charge_time_remaining` | Minutes left until full, only while charging |
| `sensor.tata_ira_ev_front_left_tyre` | Front left tyre pressure |
| `sensor.tata_ira_ev_front_right_tyre` | Front right tyre pressure |
| `sensor.tata_ira_ev_back_left_tyre` | Back left tyre pressure |
| `sensor.tata_ira_ev_back_right_tyre` | Back right tyre pressure |
| `binary_sensor.tata_ira_ev_tyre_pressure` | On when any tyre pressure is low |
| `sensor.tata_ira_ev_range` | Remaining range |
| `sensor.tata_ira_ev_odometer` | Odometer |
| `sensor.tata_ira_ev_12v_battery` | 12V battery voltage |
| `binary_sensor.tata_ira_ev_12v_battery_low` | On when the 12V battery is low |
| `sensor.tata_ira_ev_service_due` | Days until the next service |
| `sensor.tata_ira_ev_service_distance` | Kilometres until the next service |
| `sensor.tata_ira_ev_speed` | Speed from the latest status |
| `binary_sensor.tata_ira_ev_charger_connected` | On when a charger is plugged in |
| `binary_sensor.tata_ira_ev_warning` | On when the car reports a fault lamp |
| `binary_sensor.tata_ira_ev_front_left_door` | On while the front left door is open |
| `binary_sensor.tata_ira_ev_front_right_door` | On while the front right door is open |
| `binary_sensor.tata_ira_ev_rear_left_door` | On while the rear left door is open |
| `binary_sensor.tata_ira_ev_rear_right_door` | On while the rear right door is open |
| `binary_sensor.tata_ira_ev_bonnet` | On while the bonnet is open |
| `binary_sensor.tata_ira_ev_tailgate` | On while the tailgate is open |
| `device_tracker.tata_ira_ev_location` | Map of the last reported location |
| `binary_sensor.tata_ira_ev_ignition` | On while the car is switched on |
| `binary_sensor.tata_ira_ev_key_in_car` | On when the key is inside the car |
| `binary_sensor.tata_ira_ev_high_beam` | On while the high beam is on |
| `binary_sensor.tata_ira_ev_low_beam` | On while the low beam is on |
| `switch.tata_ira_ev_air_conditioning` | Starts the air conditioner for the saved duration, or stops it |
| `number.tata_ira_ev_air_conditioning_duration` | Next air-conditioning run, 0 to 30 minutes, default 10 |
| `switch.tata_ira_ev_approach_lights` | Approach lights |
| `switch.tata_ira_ev_headlights` | Headlights (position lamps) |
| `switch.tata_ira_ev_hazard_lights` | Hazard lights |
| `button.tata_ira_ev_horn` | Sound the horn once |
| `lock.tata_ira_ev_lock` | Locked or unlocked. Lock and unlock the car |
| `binary_sensor.tata_ira_ev_connected` | On while the command link is awake |
| `button.tata_ira_ev_refresh` | Read the car now |

## Example

Cool the cabin for 10 minutes:

```yaml
actions:
  - action: number.set_value
    target:
      entity_id: number.tata_ira_ev_air_conditioning_duration
    data:
      value: 10
  - action: switch.turn_on
    target:
      entity_id: switch.tata_ira_ev_air_conditioning
```

The switch stays loading until iRA.ev reports that the air conditioner has started.

## Limits

Readings are polled from iRA.ev every 30 seconds. This integration does not subscribe to the app’s live push channel.

The app also lists beep and flash. This integration does not include that command, because the car’s connection does not provide one.

## Disclaimer

Tata, iRA.ev, and the car names are trademarks of their owners. This integration is an independent Home Assistant component.
