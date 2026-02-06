#!/bin/bash
# Simple startup script for Azure App Service
# Note: Playwright is NOT available - Outlook verification is disabled in code

cd /home/site/wwwroot

# Create necessary directories
mkdir -p signatures
mkdir -p temp_uploads
mkdir -p screenshots

# Start using Python directly
python -u app.py
