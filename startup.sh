#!/bin/bash
# Start Gunicorn with proper configuration
# Install dependencies since we are using Zip Deploy (no build)
pip install -r requirements.txt

# Create necessary directories
mkdir -p signatures
mkdir -p temp_uploads
mkdir -p screenshots

gunicorn --bind=0.0.0.0:8000 --timeout 600 --workers 1 app:app
