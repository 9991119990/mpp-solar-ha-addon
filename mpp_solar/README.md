# MPP Solar Monitor Add-on

Monitor your MPP Solar PIP5048MG inverter and integrate it with Home Assistant.

## Features

- Real-time monitoring of solar panels, battery, and AC output
- Automatic MQTT discovery for easy Home Assistant integration
- Support for multiple HID devices
- Configurable update intervals
- Low resource usage

## Monitored Values

- Solar panel voltage, current, and power
- Battery voltage, capacity, and charging status
- AC output voltage, frequency, power, and load
- Inverter temperature
- System status indicators

See the documentation tab for detailed setup instructions.

## Configuration (excerpt)

```yaml
device: /dev/hidraw0
mqtt_host: core-mosquitto
mqtt_port: 1883
mqtt_username: your_mqtt_user
mqtt_password: your_mqtt_password
interval: 5
# When enabled, frames with bad CRC are discarded (default: false)
crc_strict: false
```
