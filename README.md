# Ember Mug Control

## Introduction

This mini 'application' was just something written to help interact with my Ember Mug, as the official app (at the time) was giving me a lot of issues.

After some digging around, I found [this lovely repository](https://github.com/orlopau/ember-mug) that details the hows of interacting with the mug over BLE. A couple of beers (and hours) later and this was born!

## Functionality

This application lets you do things like:
- See the status (battery percentage, charging status, current & target temperatures)
- Update various operating parameters (temperature, temperature unit, name)

### Usage

The application supports a number of different modes:

#### Scan Mode

This mode will scan for Ember Mugs with Bluetooth, and will allow the user to select one to interact with, if any are found.

```
./ember_mug_control.py scan --time 6
```
| Argument | Description |
| -------- | ----------- |
|  `scan`  | Enables scan mode for the application |
| `--time` | Sets the number of seconds to scan for Ember Mugs. Default is 5 seconds |

Once the user selects a mug, the application will then start prompting for the various commands to issue the mug, which are detailed below. 

If you'd like to skip this once you find the MAC address of the mug you would like to control, example commands are also included.

#### Connect Mode

This mode will connect to the Ember Mug (provided the MAC address) and will allow various commands to be issued to the mug.

```
./ember_mug_control.py connect --id {mug_mac_address}
```

##### Set Mug Name

Sets the mug name that is displayed in the official Ember Mug application as well as in subsequent status calls.

Note that the name must meet the following criteria:
- Be compatible with ASCII encoding.
- Not contain spaces.
- Must take less than 14 bytes.

```
./ember_mug_control.py connect --id {mug_mac_address} set-name --name Calcifer
```

| Argument   | Description |
| ---------- | ----------- |
| `set-name` | Set the desired name for the mug. |
| `--name`   | The desired name for the mug. |

##### Status

Retrieves the current status of the mug and prints out various operating information, such as name, current & target temperature, and
battery percentage.

```
./ember_mug_control.py connect --id {mug_mac_address} status
```

| Argument | Description |
| -------- | ----------- |
| `status` | Determine and print out status for the mug |

##### Set Target Temperature

Sets the target temperature of the mug. Note that this temperature should be in the mug's currently set temperature unit (one
of Celsius or Fahrenheit). The unit can be checked using the `status` command.

The temperature must fall into the following ranges:
- For Celsius
  - 32 < x < 93
- For Fahrenheit
  - 90 < x < 200

```
./ember_mug_control.py connect --id {mug_mac_address} set-target-temp --temp 80
```

| Argument          | Description |
| ----------------- | ----------- |
| `set-target-temp` | Set the target temperature for the mug. |
| `--temp`          | The temperature to set (in the mug's set temperature unit). |

##### Set Temperature Unit

Sets the temperature unit of the mug to either Celsius or Fahrenheit. This will also alter all temperature commands
for the mug to both set and retrieve temperature in the selected unit.

```
./ember_mug_control.py connect --id {mug_mac_address} set-temp-unit --unit 80
```

| Argument        | Description |
| --------------- | ----------- |
| `set-temp-unit` | Set the temperature unit for the mug. |
| `--unit`        | The temperature unit to set (either C or F). |

## Roadmap

There's a couple of things I may or may not add as time goes on, ranging from:
- Refactoring the very simple CLI to a GUI or a more complex CLI utilizing [asciimatics](https://pypi.org/project/asciimatics/)
- Adding persistence of any interacted-with mugs for quicker startup of the app with less command-line wrangling.
  - This would allow things like using the mug's name in the prompts instead of the default 'Ember Ceramic Mug' or just 'mug'.

## Remarks

This application is _definitely_ not perfect, and was written in haste. Feel free to extend this or the original documentation with any new / desired features as you stumble upon the need.

**To Warm Coffee!**
