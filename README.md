# Campus Outing Automation System

## Overview

This project is an automated system for handling campus outing requests, including PDF generation, form filling, and email notifications. It consists of a Python backend (Flask), a React frontend (for document handling), and various automation scripts.

## Prerequisites

*   Python 3.11+
*   Node.js (for frontend)
*   Docker (optional, for containerized deployment)
*   PostgreSQL database (Supabase or local)
*   Azure Blob Storage account
*   Google Cloud Project (for Gmail API)
*   Groq API Key (for AI features)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Frontend dependencies (optional):**
    ```bash
    cd doc_handle
    npm install
    cd ..
    ```

4.  **Install Playwright browsers:**
    ```bash
    playwright install chromium
    ```

## Configuration

Create a `.env` file in the root directory with the following variables:

```env
# Database
DB_HOST=your_db_host
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_PORT=5432

# Flask
FLASK_SECRET_KEY=your_secret_key
PORT=8000

# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
AZURE_STORAGE_CONTAINER=outing-submissions

# Razorpay
RAZORPAY_KEY_ID=your_key_id
RAZORPAY_KEY_SECRET=your_key_secret

# Google/Gmail
GMAIL_TOKEN_JSON=your_gmail_token_json

# Groq AI
GROQ_API_KEY=your_groq_api_key

# Admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin_password
```

## Running the Application

### Local Development

1.  **Start the backend:**
    ```bash
    python app.py
    ```
    The server will start on `http://0.0.0.0:8000`.

2.  **Start the frontend:**
    ```bash
    cd doc_handle
    npm run dev
    ```

### Docker

To build and run the container:

```bash
docker build -t campus-outing .
docker run -p 8000:8000 --env-file .env campus-outing
```

## Project Structure

*   `app.py`: Main entry point for the Flask application.
*   `form_filler/`: Contains the core logic for form automation and API endpoints.
    *   `api.py`: API routes definition.
    *   `ms_form_automation.py`: Microsoft Forms automation logic using Playwright.
    *   `azure_storage_helper.py`: Azure Blob Storage utilities.
*   `doc_handle/`: React frontend for document handling.
*   `mail_agent/`: Python scripts for handling email automation (Gmail integration).
*   `database/`: Database schema and migration scripts.
*   `tests/`: Unit and integration tests.

## Testing

To run the tests:

```bash
python -m pytest tests/
```
