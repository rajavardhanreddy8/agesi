#!/bin/bash
set -e

echo "=== Starting Azure App Service Startup Script ==="

# Navigate to app directory
cd /home/site/wwwroot

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright system dependencies (required for Chromium)
echo "Installing Playwright system dependencies..."
apt-get update
apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    fonts-liberation || echo "Some dependencies may have failed to install, continuing..."

# Install Playwright browsers
echo "Installing Playwright Chromium browser..."
export PLAYWRIGHT_BROWSERS_PATH=/home/site/playwright-browsers
playwright install chromium

# Create necessary directories
echo "Creating required directories..."
mkdir -p signatures
mkdir -p temp_uploads
mkdir -p screenshots

echo "=== Startup script completed, launching Gunicorn ==="

# Start Gunicorn
exec gunicorn --bind=0.0.0.0:8000 --timeout 600 --workers 1 --access-logfile - --error-logfile - app:app
