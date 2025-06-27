#!/usr/bin/with-contenv bashio

# Get configuration from Home Assistant
DEVICE=$(bashio::config 'device')
INTERVAL=$(bashio::config 'interval')
MQTT_HOST=$(bashio::config 'mqtt_host')
MQTT_PORT=$(bashio::config 'mqtt_port')
MQTT_USERNAME=$(bashio::config 'mqtt_username')
MQTT_PASSWORD=$(bashio::config 'mqtt_password')
MQTT_TOPIC=$(bashio::config 'mqtt_topic')
DEBUG=$(bashio::config 'debug')

# Try to get MQTT service info from HA
if bashio::services.available "mqtt"; then
    MQTT_HOST=$(bashio::services "mqtt" "host")
    MQTT_PORT=$(bashio::services "mqtt" "port")
    MQTT_USERNAME=$(bashio::services "mqtt" "username")
    MQTT_PASSWORD=$(bashio::services "mqtt" "password")
    bashio::log.info "Using MQTT service from HA: ${MQTT_HOST}:${MQTT_PORT}"
fi

# Export as environment variables
export DEVICE="${DEVICE}"
export INTERVAL="${INTERVAL}"
export MQTT_HOST="${MQTT_HOST}"
export MQTT_PORT="${MQTT_PORT}"
export MQTT_USERNAME="${MQTT_USERNAME}"
export MQTT_PASSWORD="${MQTT_PASSWORD}"
export MQTT_TOPIC="${MQTT_TOPIC}"
export DEBUG="${DEBUG}"

bashio::log.info "Starting MPP Solar Monitor..."
bashio::log.info "Device: ${DEVICE}"
bashio::log.info "MQTT Host: ${MQTT_HOST}:${MQTT_PORT}"
bashio::log.info "Update interval: ${INTERVAL}s"

# Wait for MQTT to be available
if bashio::services.available "mqtt"; then
    bashio::log.info "MQTT service available"
else
    bashio::log.warning "MQTT service not available, using configured host"
fi

# Check device availability  
if [ -e "${DEVICE}" ]; then
    bashio::log.info "Device ${DEVICE} found"
    ls -la "${DEVICE}" || true
else
    bashio::log.warning "Device ${DEVICE} not found"
    # List all hidraw devices for debugging
    bashio::log.info "Available hidraw devices:"
    ls -la /dev/hidraw* 2>/dev/null || bashio::log.info "No hidraw devices found"
fi

# Run the Python application
exec python3 /app/mpp_solar_monitor.py