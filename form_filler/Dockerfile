# Use official Playwright Python image (comes with browsers pre-installed)
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Install additional system dependencies if needed (e.g., for psycopg2)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage caching
COPY requirements.txt .

# Install Python dependencies
# Chunk 1: Small/Core dependencies
RUN pip install --no-cache-dir python-dotenv requests flask flask-cors gunicorn psycopg2-binary bcrypt cryptography PyJWT

# Chunk 2a: Supabase and network libs
RUN pip install --no-cache-dir "supabase>=2.10.0" httpx razorpay

# Chunk 2b: PDF generation
RUN pip install --no-cache-dir reportlab

# Chunk 2c: Image processing
RUN pip install --no-cache-dir Pillow

# Chunk 3: Ensure everything from requirements is covered (will be fast if satisfied)
RUN pip install --no-cache-dir -r requirements.txt

# (Browsers are already pre-installed in this image)
# Reduced size: Commenting out install-deps as base image is likely sufficient
# RUN playwright install-deps chromium

# Copy the rest of the application
COPY . .

# Expose port (Cloud Run sets $PORT env var, we'll default to 8080)
ENV PORT=8080

# Command to run the application using Gunicorn
# Adjust workers based on Cloud Run memory settings (2-4 usually good)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 api:app
