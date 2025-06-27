# MPP Solar Monitor Documentation

## Overview

This add-on monitors MPP Solar PIP5048MG inverters and publishes data to Home Assistant via MQTT.

## Installation

1. Add this repository to your Home Assistant Add-on Store
2. Install the "MPP Solar Monitor" add-on
3. Configure the add-on (see Configuration section)
4. Start the add-on

## Configuration

### Required Settings

- **device**: The HID device path for your inverter (default: `/dev/hidraw0`)
  - Common values: `/dev/hidraw0`, `/dev/hidraw1`, `/dev/hidraw2`
  - Check your logs to find the correct device

- **mqtt_host**: MQTT broker hostname (default: `core-mosquitto`)
  - Use `core-mosquitto` for the Mosquitto add-on
  - Use IP address for external MQTT brokers

### Optional Settings

- **interval**: Update interval in seconds (default: 30, min: 10, max: 300)
- **mqtt_port**: MQTT broker port (default: 1883)
- **mqtt_username**: MQTT username (leave empty if not required)
- **mqtt_password**: MQTT password (leave empty if not required)
- **mqtt_topic**: Base MQTT topic (default: `mpp_solar`)
- **debug**: Enable debug logging (default: false)

## Finding Your Device

1. Connect your MPP Solar inverter via USB
2. Check the add-on logs for device detection
3. Or use SSH to run: `ls -la /dev/hidraw*`
4. The inverter typically shows as `/dev/hidraw0`, `/dev/hidraw1`, or `/dev/hidraw2`

## Home Assistant Integration

The add-on automatically creates entities via MQTT discovery:

### Sensors
- `sensor.mpp_solar_pip5048mg_pv_input_power` - Solar panel power (W)
- `sensor.mpp_solar_pip5048mg_battery_voltage` - Battery voltage (V)
- `sensor.mpp_solar_pip5048mg_battery_capacity` - Battery capacity (%)
- `sensor.mpp_solar_pip5048mg_ac_output_power` - AC output power (W)
- `sensor.mpp_solar_pip5048mg_inverter_temperature` - Inverter temperature (°C)

### Binary Sensors
- `binary_sensor.mpp_solar_pip5048mg_load_on` - Load status
- `binary_sensor.mpp_solar_pip5048mg_solar_charging` - Solar charging status
- `binary_sensor.mpp_solar_pip5048mg_ac_charging` - AC charging status

## Example Lovelace Card

```yaml
type: entities
title: MPP Solar Inverter
entities:
  - entity: sensor.mpp_solar_pip5048mg_pv_input_power
    name: Solar Power
  - entity: sensor.mpp_solar_pip5048mg_battery_voltage
    name: Battery Voltage
  - entity: sensor.mpp_solar_pip5048mg_battery_capacity
    name: Battery Level
  - entity: sensor.mpp_solar_pip5048mg_ac_output_power
    name: Output Power
  - entity: binary_sensor.mpp_solar_pip5048mg_solar_charging
    name: Solar Charging
```

## Troubleshooting

### Device Not Found
- Ensure the USB cable is properly connected
- Check device permissions in the logs
- Try different hidraw devices in configuration

### MQTT Connection Failed
- Verify MQTT broker is running
- Check username/password if authentication is enabled
- Ensure correct hostname/IP and port

### No Data Published
- Check add-on logs for errors
- Verify the inverter is powered on
- Ensure correct device path in configuration

## Support

For issues and feature requests, please visit the GitHub repository.