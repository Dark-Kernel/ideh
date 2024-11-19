# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire project
COPY . .

# Generate self-signed SSL certificate if not provided
RUN if [ ! -f cert.pem ] || [ ! -f key.pem ]; then \
    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem \
    -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/OU=IT/CN=localhost"; \
    fi

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a directory for potential user credentials
RUN mkdir -p /app/credentials

# Expose the HTTPS port
EXPOSE 443

# Run the application with gunicorn using HTTPS
CMD ["gunicorn", "--certfile=cert.pem", "--keyfile=key.pem", \
     "--bind", "0.0.0.0:443", "app:app", "--workers", "3"]
