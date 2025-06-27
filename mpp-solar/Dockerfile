ARG BUILD_FROM
FROM $BUILD_FROM

# Install system dependencies
RUN apk add --no-cache \
    python3-dev \
    py3-pip \
    gcc \
    musl-dev \
    linux-headers

# Set workdir
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY *.py ./
COPY run.sh /

# Make run script executable
RUN chmod a+x /run.sh

# Run script as entry point
CMD [ "/run.sh" ]