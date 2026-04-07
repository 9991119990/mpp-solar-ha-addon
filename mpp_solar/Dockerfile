ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.11-alpine3.18
ARG BUILD_VERSION=dev
ARG BUILD_ARCH=unknown
FROM $BUILD_FROM

ARG BUILD_VERSION
ARG BUILD_ARCH

LABEL \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="app" \
  io.hass.arch="${BUILD_ARCH}"

# Set workdir
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY mpp_solar_monitor.py ./
COPY run.sh /

# Make run script executable
RUN chmod a+x /run.sh

# Run script as entry point
CMD [ "/run.sh" ]
