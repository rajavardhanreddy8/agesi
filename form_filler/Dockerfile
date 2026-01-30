# Use official Python image
FROM python:3.11-slim

# Install system dependencies for Playwright and Gunicorn
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium only is enough for this app)
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy the rest of the application
COPY . .

# Expose port (Cloud Run sets $PORT env var, we'll default to 8080)
ENV PORT=8080

# Command to run the application using Gunicorn
# Adjust workers based on Cloud Run memory settings (2-4 usually good)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 api:app
