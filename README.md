# MPP Solar Home Assistant Add-on v2.0.0

Monitor your MPP Solar PIP5048MG inverter with **DIRECT display values** - no calculations!

## 🎯 Major Discovery - Version 2.0.0
**MPP Solar stores actual PV power DIRECTLY in position 19** - just like EASUN inverters!
- **98.2% accuracy** with real display values
- **No calculations or correction factors**
- **Direct reading from QPIGS response position 19**

## Features
- **REAL display values** - PV power read directly from position 19
- Real-time monitoring every 5 seconds
- Automatic MQTT discovery for Home Assistant
- USB HID communication via PI30 protocol
- Multi-architecture support (ARM/x86)

## Installation

1. Add this repository to Home Assistant:
   ```
   https://github.com/9991119990/mpp-solar-ha-addon
   ```
2. Install "MPP Solar Monitor" from the add-on store
3. Configure your device settings
4. Start the add-on

## Configuration

```yaml
device: /dev/hidraw0
mqtt_host: core-mosquitto
mqtt_port: 1883
mqtt_username: your_mqtt_user
mqtt_password: your_mqtt_password
update_interval: 5
```

## Available Sensors

- **sensor.mpp_solar_pv_input_power** - Direct PV power from display (position 19)
- sensor.mpp_solar_battery_voltage
- sensor.mpp_solar_battery_capacity
- sensor.mpp_solar_ac_output_power
- sensor.mpp_solar_inverter_temperature
- And more...

## Changelog

### v2.0.0 - FINAL PRODUCTION VERSION
- **BREAKTHROUGH**: Found direct PV power value in position 19
- Removed all calculations and correction factors
- 98.2% accuracy with real display values
- Same implementation as EASUN inverters

### Previous versions
- v1.0.0-1.0.12: Various calculation attempts (deprecated)

## Technical Details

The inverter communicates using the PI30 protocol over USB HID. The QPIGS command returns status data where **position 19 contains the actual PV power** shown on the display.

Example:
- Display shows: 444W
- Position 19 value: 436W
- Accuracy: 98.2%

## Support

For issues or questions, please visit:
https://github.com/9991119990/mpp-solar-ha-addon/issues