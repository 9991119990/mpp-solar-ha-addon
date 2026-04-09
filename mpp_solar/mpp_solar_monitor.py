#!/usr/bin/env python3
"""
MPP Solar Monitor for Home Assistant
Reads data from MPP Solar inverter and publishes to MQTT
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timezone
import paho.mqtt.client as mqtt

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

class MPPSolarMonitor:
    def __init__(self):
        # Get config from environment
        self.device = os.environ.get('DEVICE', '/dev/hidraw0')
        self.interval = int(os.environ.get('INTERVAL', '30'))
        self.mqtt_host = os.environ.get('MQTT_HOST', 'localhost')
        self.mqtt_port = int(os.environ.get('MQTT_PORT', '1883'))
        self.mqtt_user = os.environ.get('MQTT_USERNAME', '')
        self.mqtt_pass = os.environ.get('MQTT_PASSWORD', '')
        self.mqtt_topic = os.environ.get('MQTT_TOPIC', 'mpp_solar')
        self.debug = os.environ.get('DEBUG', 'false').lower() == 'true'
        self.crc_strict = os.environ.get('CRC_STRICT', 'false').lower() == 'true'
        
        if self.debug:
            logger.setLevel(logging.DEBUG)
            
        logger.info("MPP Solar Monitor starting...")
        logger.info(f"Device: {self.device}")
        logger.info(f"MQTT: {self.mqtt_host}:{self.mqtt_port}")
        logger.info(f"Topic: {self.mqtt_topic}")
        logger.info(f"Interval: {self.interval}s")
        
        self.mqtt_client = None
        self.device_available = False
        self.response_buffer = b""

    def get_read_deadline_seconds(self) -> float:
        """Bound inverter read time so the loop can stay responsive."""
        return max(1.2, min(2.0, self.interval * 0.4))

    def get_poll_timeout_seconds(self) -> float:
        """Short poll slices let us stop as soon as a full frame is available."""
        return max(0.05, min(0.2, self.get_read_deadline_seconds() / 4))

    def compute_cycle_sleep(self, started_at: float, finished_at: float | None = None) -> float:
        """Sleep only for the remainder of the configured interval."""
        if finished_at is None:
            finished_at = time.monotonic()
        elapsed = max(0.0, finished_at - started_at)
        return max(0.0, self.interval - elapsed)

    def has_complete_response_frame(self, response: bytes) -> bool:
        """Return True only when the full '(payload)CRC\\r' frame is present."""
        if not response:
            return False
        start = response.find(b'(')
        if start == -1:
            return False
        end = response.find(b')', start + 1)
        if end == -1:
            return False
        if end + 3 >= len(response):
            return False
        return response[end + 3:end + 4] == b'\r'

    def extract_complete_response_frame(self, response: bytes) -> tuple[bytes | None, bytes]:
        """Extract one complete frame and preserve any remaining bytes."""
        if not response:
            return None, b""

        start = response.find(b'(')
        if start == -1:
            return None, b""

        if start > 0:
            response = response[start:]

        end = response.find(b')', 1)
        if end == -1 or end + 3 >= len(response):
            return None, response

        if response[end + 3:end + 4] != b'\r':
            return None, response

        frame = response[:end + 4]
        remaining = response[end + 4:]
        next_start = remaining.find(b'(')
        if next_start > 0:
            remaining = remaining[next_start:]
        return frame, remaining

    def extract_values_from_response(self, response: bytes) -> list[str] | None:
        """Extract QPIGS values from a complete or partial ASCII response."""
        if not response:
            return None

        start = response.rfind(b'(')
        if start == -1:
            return None

        payload = response[start:]
        text = payload.decode('ascii', errors='ignore').strip()
        if not text.startswith('('):
            return None

        end_pos = text.find(')')
        if end_pos > 0:
            data_str = text[1:end_pos]
        else:
            data_str = text[1:].rstrip('\r\n')

        values = data_str.split()
        if len(values) >= 17:
            return values
        return None

    def _looks_like_status_field(self, s: str) -> bool:
        """Heuristic: PI30 status is typically an 8-bit string of 0/1.
        Accept 8..12 chars consisting only of 0/1 to be tolerant across variants."""
        if not isinstance(s, str):
            try:
                s = str(s)
            except Exception:
                return False
        if len(s) < 8 or len(s) > 12:
            return False
        return set(s) <= {"0", "1"}
        
    def crc16_xmodem(self, data):
        """Calculate CRC16 XMODEM"""
        crc = 0x0000
        for byte in data:
            crc ^= byte << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc <<= 1
                crc &= 0xFFFF
        return crc
    
    def create_command(self, cmd_str):
        """Create command with CRC"""
        cmd_bytes = cmd_str.encode('ascii')
        crc = self.crc16_xmodem(cmd_bytes)
        return cmd_bytes + crc.to_bytes(2, 'big') + b'\r'
    
    def wait_for_device(self):
        """Wait for device to be available"""
        retry_count = 0
        while retry_count < 30:  # Try for 5 minutes
            if os.path.exists(self.device):
                try:
                    # Check permissions (no chmod in container)
                    if not os.access(self.device, os.R_OK | os.W_OK):
                        logger.warning(f"Device {self.device} not accessible")
                    else:
                        logger.info(f"Device {self.device} found and accessible")
                        return True
                except Exception as e:
                    logger.warning(f"Cannot access device: {e}")
            
            if retry_count == 0:
                logger.info(f"Waiting for device {self.device}...")
            
            time.sleep(10)
            retry_count += 1
            
        logger.error(f"Device {self.device} not found after 5 minutes")
        return False
    
    def read_inverter_data(self):
        """Read data from inverter via HID"""
        try:
            logger.debug(f"Opening device {self.device}")
            
            # Use non-blocking approach with timeout
            import select
            import os
            
            fd = os.open(self.device, os.O_RDWR | os.O_NONBLOCK)
            try:
                logger.debug("Device opened successfully")
                
                # Send QPIGS command
                cmd = self.create_command('QPIGS')
                logger.debug(f"Sending QPIGS command: {cmd.hex()}")
                os.write(fd, cmd)
                
                # Read until full frame is available or deadline is reached
                logger.debug("Waiting for response...")
                response = self.response_buffer
                deadline = time.monotonic() + self.get_read_deadline_seconds()
                poll_timeout = self.get_poll_timeout_seconds()
                frame = None

                while time.monotonic() < deadline:
                    frame, response = self.extract_complete_response_frame(response)
                    if frame is not None:
                        break

                    remaining = max(0.0, deadline - time.monotonic())
                    ready, _, _ = select.select([fd], [], [], min(poll_timeout, remaining))
                    if not ready:
                        continue

                    chunk = os.read(fd, 512)
                    if not chunk:
                        continue

                    response += chunk
                    logger.debug(f"Received chunk: {len(chunk)} bytes, total={len(response)}")

                    frame, response = self.extract_complete_response_frame(response)
                    if frame is not None:
                        break

                self.response_buffer = response[-512:]

                if frame is not None:
                    response = frame
                    logger.debug(f"Received response: {len(response)} bytes")

                    if len(response) > 10:
                        logger.debug(f"Response hex: {response[:80].hex()}")

                        # Find frame boundaries in raw bytes and verify CRC if present
                        try:
                            start = response.find(b'(')
                            end = response.find(b')', start + 1)
                            if start == -1 or end == -1 or end + 3 > len(response):
                                logger.warning("Incomplete response frame, skipping this cycle")
                                return None

                            frame = response[start:end + 1]  # includes parentheses
                            crc_bytes = response[end + 1:end + 3]
                            expected_crc = int.from_bytes(crc_bytes, 'big')

                            computed_crc = self.crc16_xmodem(frame)
                            if computed_crc != expected_crc:
                                logger.warning(
                                    f"CRC mismatch: expected=0x{expected_crc:04X} computed=0x{computed_crc:04X}"
                                )
                                if self.crc_strict:
                                    return None

                            # Decode ASCII payload between parentheses
                            text = frame.decode('ascii', errors='ignore')
                            logger.debug(f"Decoded text: {text[:100]}")
                            if not text.startswith('(') or not text.endswith(')'):
                                logger.warning("Malformed frame text, skipping")
                                return None

                            data_str = text[1:-1]
                            values = data_str.split()
                            logger.debug(f"Parsed values count: {len(values)}")

                            if len(values) >= 17:
                                logger.debug("Successfully parsed inverter data")
                                return self.parse_qpigs(values)
                            else:
                                logger.warning(f"Invalid response length: {len(values)} (need >=17)")
                                logger.warning(f"Values: {values}")
                        except Exception as e:
                            logger.warning(f"Frame/CRC parse error: {e}")
                    else:
                        logger.warning(f"Short response: {len(response)} bytes")
                        if response:
                            logger.warning(f"Response hex: {response.hex()}")
                elif response:
                    values = self.extract_values_from_response(response)
                    if values is not None:
                        logger.warning(f"Using partial inverter response with {len(values)} values")
                        logger.debug(f"Partial response hex: {response[:80].hex()}")
                        return self.parse_qpigs(values)
                    logger.warning("Incomplete response frame, skipping this cycle")
                else:
                    logger.warning(
                        f"No response from inverter within {self.get_read_deadline_seconds():.2f}s timeout"
                    )
                    
            finally:
                os.close(fd)
                    
        except FileNotFoundError:
            logger.error(f"Device {self.device} not found")
            self.device_available = False
        except Exception as e:
            logger.error(f"Error reading inverter: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            
        return None
    
    def parse_qpigs(self, values):
        """Parse QPIGS response into dict"""
        try:
            # Ensure minimum length; don't pad with artificial zeros
            if len(values) < 17:
                logger.warning(f"Too few values in QPIGS: {len(values)}")
                return None

            if self.debug:
                logger.debug(f"QPIGS values: {values}")

            # Detect status index first (variant-dependent)
            status_idx = None
            if len(values) > 20 and self._looks_like_status_field(values[20]):
                status_idx = 20
            elif len(values) > 16 and self._looks_like_status_field(values[16]):
                status_idx = 16

            # Map battery discharge current index based on detected status layout
            # If status at 20 → discharge current typically at 16 (older mapping that worked for you)
            # If status at 16 → discharge current at 15 (newer PI30 mapping)
            if status_idx == 20 and len(values) > 16:
                batt_discharge_idx = 16
            elif status_idx == 16 and len(values) > 15:
                batt_discharge_idx = 15
            else:
                # Fallback: prefer 15 if present else 16
                batt_discharge_idx = 15 if len(values) > 15 else (16 if len(values) > 16 else None)

            data = {
                # AC Input
                'ac_input_voltage': float(values[0]),
                'ac_input_frequency': float(values[1]),
                
                # AC Output
                'ac_output_voltage': float(values[2]),
                'ac_output_frequency': float(values[3]),
                # Map according to PI30: [4]=apparent (VA), [5]=active (W)
                'ac_output_apparent_power': int(values[4]),
                'ac_output_power': int(values[5]),
                'ac_output_load': int(values[6]),
                
                # Bus
                'bus_voltage': int(values[7]),
                
                # Battery
                'battery_voltage': float(values[8]),
                'battery_charging_current': int(values[9]) if len(values) > 9 else 0,
                'battery_capacity': int(values[10]) if len(values) > 10 else 0,
                # Battery discharge current: resolved above from detected layout
                'battery_discharge_current': int(values[batt_discharge_idx]) if batt_discharge_idx is not None else 0,
                
                # Temperature
                'inverter_temperature': int(values[11]) if len(values) > 11 else 0,
                
                # PV
                'pv_input_current': float(values[12]) if len(values) > 12 else 0.0,
                'pv_input_voltage': float(values[13]) if len(values) > 13 else 0.0,
                'battery_scc_voltage': float(values[14]) if len(values) > 14 else 0.0,
                
                # Status determined by detection; fallback to zeros
                'device_status': (values[status_idx] if status_idx is not None else '00000000'),
            }
            
            # MPP Solar PV power - DIRECT VALUE IN POSITION 19 (FINAL VERSION 2.0.0)
            # Direct reading from position 19 - same as EASUN inverters
            pv_power_set = False
            if len(values) > 19:
                try:
                    data['pv_input_power'] = int(values[19])
                    pv_power_set = True
                    logger.debug(f"PV power from pos[19]: {data['pv_input_power']}W")
                except Exception as e:
                    logger.debug(f"Failed to parse PV power from pos[19]: {e}")
            # Safe fallback when position 19 is missing or unparsable
            if not pv_power_set:
                try:
                    calc = int(round(data['pv_input_voltage'] * data['pv_input_current']))
                except Exception:
                    calc = 0
                data['pv_input_power'] = calc
                if self.debug:
                    logger.debug(
                        f"PV power fallback V*I: {data['pv_input_voltage']}V * {data['pv_input_current']}A = {calc}W"
                    )
            
            # Battery power (positive = charging, negative = discharging)
            battery_current = data['battery_charging_current'] - data['battery_discharge_current']
            data['battery_power'] = round(data['battery_voltage'] * battery_current, 1)
            
            # Parse status bits if available
            if data['device_status'] and len(data['device_status']) >= 8:
                status = data['device_status']
                data['load_on'] = status[4] == '1'
                data['scc_charging'] = status[6] == '1'
                data['ac_charging'] = status[7] == '1'
            else:
                data['load_on'] = False
                data['scc_charging'] = False
                data['ac_charging'] = False
                
            return data
            
        except Exception as e:
            logger.error(f"Error parsing QPIGS: {e}")
            logger.debug(f"Raw values: {values}")
            return None
    
    def setup_mqtt(self):
        """Setup MQTT connection"""
        try:
            # Use MQTT v1 callback API for compatibility with current callbacks
            self.mqtt_client = mqtt.Client(
                client_id=f"mpp_solar_{os.getpid()}",
                protocol=mqtt.MQTTv311,
                callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
            )
            # Set LWT before connecting so broker marks offline on unexpected disconnects
            self.mqtt_client.will_set(
                f"{self.mqtt_topic}/availability",
                "offline",
                qos=1,
                retain=True
            )
            
            # Set authentication if provided
            if self.mqtt_user and self.mqtt_pass:
                self.mqtt_client.username_pw_set(self.mqtt_user, self.mqtt_pass)
                logger.info(f"Using MQTT authentication for user: {self.mqtt_user}")
            else:
                logger.info("No MQTT authentication provided, trying anonymous")
                
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    logger.info("Connected to MQTT broker")
                    # Publish online status
                    client.publish(
                        f"{self.mqtt_topic}/availability",
                        "online",
                        qos=1,
                        retain=True
                    )
                    # Publish discovery
                    self.publish_discovery()
                else:
                    logger.error(f"MQTT connection failed with code: {rc}")
                    
            def on_disconnect(client, userdata, rc):
                if rc != 0:
                    logger.warning(f"Unexpected MQTT disconnection: {rc}")
                    
            self.mqtt_client.on_connect = on_connect
            self.mqtt_client.on_disconnect = on_disconnect
            
            # Connect with retry
            connected = False
            for i in range(5):
                try:
                    self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, 60)
                    self.mqtt_client.loop_start()
                    connected = True
                    break
                except Exception as e:
                    logger.warning(f"MQTT connection attempt {i+1} failed: {e}")
                    time.sleep(5)
                    
            return connected
            
        except Exception as e:
            logger.error(f"MQTT setup failed: {e}")
            return False
    
    def publish_discovery(self):
        """Publish Home Assistant MQTT discovery messages"""
        device_info = {
            "identifiers": ["mpp_solar_pip5048mg"],
            "name": "MPP Solar PIP5048MG",
            "model": "PIP5048MG",
            "manufacturer": "MPP Solar",
            "sw_version": "2.0.14"
        }
        
        # Sensor definitions
        sensors = [
            # Power sensors
            {
                "id": "pv_input_power",
                "name": "PV Input Power",
                "unit": "W",
                "icon": "mdi:solar-power",
                "device_class": "power",
                "state_class": "measurement"
            },
            {
                "id": "ac_output_power",
                "name": "AC Output Power",
                "unit": "W",
                "icon": "mdi:flash",
                "device_class": "power",
                "state_class": "measurement"
            },
            {
                "id": "battery_power",
                "name": "Battery Power",
                "unit": "W",
                "icon": "mdi:battery-charging",
                "device_class": "power",
                "state_class": "measurement"
            },
            
            # Voltage sensors
            {
                "id": "pv_input_voltage",
                "name": "PV Input Voltage",
                "unit": "V",
                "icon": "mdi:flash",
                "device_class": "voltage",
                "state_class": "measurement"
            },
            {
                "id": "battery_voltage",
                "name": "Battery Voltage",
                "unit": "V",
                "icon": "mdi:battery",
                "device_class": "voltage",
                "state_class": "measurement"
            },
            {
                "id": "ac_output_voltage",
                "name": "AC Output Voltage",
                "unit": "V",
                "icon": "mdi:power-socket",
                "device_class": "voltage",
                "state_class": "measurement"
            },
            
            # Other sensors
            {
                "id": "battery_capacity",
                "name": "Battery Capacity",
                "unit": "%",
                "icon": "mdi:battery-50",
                "device_class": "battery",
                "state_class": "measurement"
            },
            {
                "id": "ac_output_load",
                "name": "AC Output Load",
                "unit": "%",
                "icon": "mdi:gauge",
                "state_class": "measurement"
            },
            {
                "id": "inverter_temperature",
                "name": "Inverter Temperature",
                "unit": "°C",
                "icon": "mdi:thermometer",
                "device_class": "temperature",
                "state_class": "measurement"
            },
        ]
        
        # Binary sensors
        binary_sensors = [
            {
                "id": "load_on",
                "name": "Load On",
                "icon": "mdi:power",
                "device_class": "power"
            },
            {
                "id": "scc_charging",
                "name": "Solar Charging",
                "icon": "mdi:solar-power",
                "device_class": "battery_charging"
            },
            {
                "id": "ac_charging",
                "name": "AC Charging",
                "icon": "mdi:power-plug",
                "device_class": "battery_charging"
            },
        ]
        
        # Publish sensor discovery
        for sensor in sensors:
            topic = f"homeassistant/sensor/mpp_solar/{sensor['id']}/config"
            config = {
                "name": sensor["name"],
                "state_topic": f"{self.mqtt_topic}/state",
                "value_template": f"{{{{ value_json.{sensor['id']} }}}}",
                "unique_id": f"mpp_solar_{sensor['id']}",
                "device": device_info,
                "unit_of_measurement": sensor["unit"],
                "icon": sensor["icon"],
                "availability_topic": f"{self.mqtt_topic}/availability"
            }
            
            if "device_class" in sensor:
                config["device_class"] = sensor["device_class"]
            if "state_class" in sensor:
                config["state_class"] = sensor["state_class"]
                
            self.mqtt_client.publish(topic, json.dumps(config), qos=1, retain=True)
            logger.debug(f"Published discovery for {sensor['id']}")
            
        # Publish binary sensor discovery
        for sensor in binary_sensors:
            topic = f"homeassistant/binary_sensor/mpp_solar/{sensor['id']}/config"
            config = {
                "name": sensor["name"],
                "state_topic": f"{self.mqtt_topic}/state",
                "value_template": f"{{{{ 'ON' if value_json.{sensor['id']} else 'OFF' }}}}",
                "unique_id": f"mpp_solar_{sensor['id']}",
                "device": device_info,
                "icon": sensor["icon"],
                "availability_topic": f"{self.mqtt_topic}/availability"
            }
            
            if "device_class" in sensor:
                config["device_class"] = sensor["device_class"]
                
            self.mqtt_client.publish(topic, json.dumps(config), qos=1, retain=True)
            logger.debug(f"Published discovery for binary_{sensor['id']}")
            
        logger.info("Published MQTT discovery messages")
    
    def publish_data(self, data):
        """Publish data to MQTT"""
        if self.mqtt_client and data:
            # Add timestamp
            data['timestamp'] = datetime.now(timezone.utc).isoformat()
            
            # Publish state
            self.mqtt_client.publish(
                f"{self.mqtt_topic}/state",
                json.dumps(data),
                retain=False
            )
            
            # Log summary
            logger.info(
                f"Published: PV={data['pv_input_power']}W, "
                f"Battery={data['battery_voltage']:.1f}V/{data['battery_capacity']}%, "
                f"Load={data['ac_output_power']}W, "
                f"Temp={data['inverter_temperature']}°C"
            )
    
    def run(self):
        """Main loop"""
        logger.info("Starting MPP Solar Monitor...")
        
        # Wait for device
        if not self.wait_for_device():
            logger.error("Device not available, exiting")
            return 1
            
        # Setup MQTT
        if not self.setup_mqtt():
            logger.error("Failed to setup MQTT")
            return 1
            
        # Wait for MQTT connection
        time.sleep(2)
        
        # Main loop
        error_count = 0
        logger.info("Starting main monitoring loop...")
        
        while True:
            cycle_started = time.monotonic()
            try:
                logger.debug("Reading inverter data...")
                # Read inverter data
                read_started = time.monotonic()
                data = self.read_inverter_data()
                read_finished = time.monotonic()
                read_elapsed = read_finished - read_started
                
                if data:
                    self.publish_data(data)
                    error_count = 0
                else:
                    error_count += 1
                    logger.warning(f"No data from inverter (error count: {error_count})")
                    
                    # Check if device still exists
                    if error_count > 5 and not os.path.exists(self.device):
                        logger.error("Device disappeared, waiting for reconnection...")
                        if not self.wait_for_device():
                            break
                        error_count = 0

                if self.debug:
                    logger.debug(
                        f"Cycle timings: read={read_elapsed:.2f}s total={time.monotonic() - cycle_started:.2f}s"
                    )
                    
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                error_count += 1
                
            # Wait for next cycle
            time.sleep(self.compute_cycle_sleep(cycle_started))
        
        # Cleanup
        if self.mqtt_client:
            self.mqtt_client.publish(
                f"{self.mqtt_topic}/availability",
                "offline",
                retain=True
            )
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            
        return 0

if __name__ == "__main__":
    monitor = MPPSolarMonitor()
    sys.exit(monitor.run())
