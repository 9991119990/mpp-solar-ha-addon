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
CRC_STRICT=$(bashio::config 'crc_strict')

# Try to get MQTT service info from HA (only if not configured manually)
if bashio::services.available "mqtt" && [ "${MQTT_HOST}" = "core-mosquitto" ] && [ -z "${MQTT_USERNAME}" ]; then
    HA_MQTT_HOST=$(bashio::services "mqtt" "host")
    HA_MQTT_PORT=$(bashio::services "mqtt" "port")
    HA_MQTT_USERNAME=$(bashio::services "mqtt" "username")
    HA_MQTT_PASSWORD=$(bashio::services "mqtt" "password")
    
    if [ -n "${HA_MQTT_USERNAME}" ]; then
        MQTT_HOST="${HA_MQTT_HOST}"
        MQTT_PORT="${HA_MQTT_PORT}"
        MQTT_USERNAME="${HA_MQTT_USERNAME}"
        MQTT_PASSWORD="${HA_MQTT_PASSWORD}"
        bashio::log.info "Using MQTT service from HA: ${MQTT_HOST}:${MQTT_PORT} with user ${MQTT_USERNAME}"
    else
        bashio::log.info "Using configured MQTT: ${MQTT_HOST}:${MQTT_PORT} with user ${MQTT_USERNAME}"
    fi
else
    bashio::log.info "Using configured MQTT: ${MQTT_HOST}:${MQTT_PORT} with user ${MQTT_USERNAME}"
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
export CRC_STRICT="${CRC_STRICT}"

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
