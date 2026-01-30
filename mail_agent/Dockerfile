FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if needed (none strictly for these python packages, but good practice)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set unbuffered output for logging
ENV PYTHONUNBUFFERED=1

# Command to run the agent
CMD ["python", "bridge.py"]
