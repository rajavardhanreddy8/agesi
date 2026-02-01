#!/bin/bash
# Install dependencies (just in case)
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Start Gunicorn
# Pointing to form_filler/api.py where 'app' is the Flask instance
gunicorn --bind=0.0.0.0:8000 --timeout 600 --chdir form_filler api:app
