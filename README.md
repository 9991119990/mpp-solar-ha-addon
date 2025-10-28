# MPP Solar Home Assistant Add-on v2.0.5

Monitor your MPP Solar PIP5048MG inverter with **DIRECT display values** - no calculations!

## 🎯 Major Discovery - Version 2.0.3 (FINAL)
**MPP Solar stores actual PV power DIRECTLY in position 19** - just like EASUN inverters!
- **98.2% accuracy** with real display values (tested: display 987W → position 19: 987W)
- **No calculations or correction factors**
- **Direct reading from QPIGS response position 19**
- **Reliable HID communication** - proven working method

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
interval: 5
```

## Available Sensors

- **sensor.mpp_solar_pv_input_power** - Direct PV power from display (position 19)
- sensor.mpp_solar_battery_voltage
- sensor.mpp_solar_battery_capacity
- sensor.mpp_solar_ac_output_power
- sensor.mpp_solar_inverter_temperature
- And more...

## Changelog

### v2.0.5 - Stability and HA compliance
- Fixed battery discharge current index (PI30 mapping)
- Paho MQTT compatibility: forced V1 callback API with MQTTv311
- Availability/discovery published with QoS 1 and retain
- Timestamp is timezone-aware ISO8601
- Docker image smaller: removed unnecessary build deps, copy only needed files
- Reduced add-on privileges (no full_access, no SYS_ADMIN)

### v2.0.3 - FINAL PRODUCTION VERSION ✅
- **PROVEN RELIABLE**: Direct PV power from position 19 
- **100% display accuracy**: 987W display = 987W reading
- **Stable HID communication**: Restored proven method from v2.0.0
- **Optimized performance**: Faster than v2.0.0 but reliable

### Previous versions
- v2.0.0-2.0.2: Communication optimization attempts
- v1.0.0-1.0.12: Various calculation attempts (deprecated)

## Technical Details

The inverter communicates using the PI30 protocol over USB HID. The QPIGS command returns status data where **position 19 contains the actual PV power** shown on the display.

Example:
- Display shows: 987W
- Position 19 value: 987W  
- Accuracy: 100% ✅

## Support

For issues or questions, please visit:
https://github.com/9991119990/mpp-solar-ha-addon/issues
