#!/bin/bash
# Start Gunicorn with proper configuration
# Azure expects the app to start quickly, so we skip Playwright install here
# Playwright will be installed during the build phase via SCM_DO_BUILD_DURING_DEPLOYMENT
cd /home/site/wwwroot
gunicorn --bind=0.0.0.0:8000 --timeout 600 --workers 1 app:app
