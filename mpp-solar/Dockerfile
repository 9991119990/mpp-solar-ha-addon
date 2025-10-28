ARG BUILD_FROM
FROM $BUILD_FROM

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
