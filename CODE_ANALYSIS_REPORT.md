# Comprehensive Code Analysis Report

This report provides a detailed, file-by-file analysis of the Campus Outing Automation System.

## 1. Core Backend Files

### `app.py`
**Summary**: The main entry point for the Flask application.
**Analysis**:
*   **Imports**: Imports `form_filler.api` and runs the app.
*   **Issues**:
    *   Hardcoded `host="0.0.0.0"` and port handling is basic.
    *   No error handling for import failures (fixed in recent patch).
**Recommendations**:
*   Use a production WSGI server (Gunicorn) configuration file instead of running `app.run()` directly in production, although `if __name__ == "__main__":` protects it.

### `form_filler/api.py`
**Summary**: Contains all API routes for authentication, form submission, PDF generation, and admin management.
**Analysis**:
*   **Security Risk**: Hardcoded `JWT_SECRET` fallback (`'your-secret-key-change-this'`) and `ADMIN_PASSWORD` fallback.
*   **Architecture**: Uses a global `automation_tasks` dictionary and `queue.Queue`. This is stateful and will break if the app restarts or scales to multiple workers.
*   **Code Quality**:
    *   Duplicate logic for `load_dotenv`.
    *   Implicit dependency on `form_filler.ms_form_automation` which might fail if Playwright isn't installed (handled by try/except but risky).
    *   Hardcoded IP `127.0.0.1` in `auto_submit_from_email`.
    *   Admin logic (`admin_login_route`) has a "temporary fix" comment for direct password checking, bypassing hashing.
**Recommendations**:
*   Move task state to a persistent store (Redis/Database).
*   Remove all hardcoded secrets.
*   Implement proper password hashing for Admin.

### `form_filler/auth_system_v2.py`
**Summary**: Handles user authentication using Supabase and JWT.
**Analysis**:
*   **CRITICAL SECURITY FLAW**: `encrypt_outlook_password` returns the password **as-is (raw text)**. `decrypt_outlook_password` tries to decrypt but falls back to raw text. This means Outlook passwords are stored in plain text in the database.
*   **Security**: Uses `bcrypt` for user passwords (good).
*   **Logic**: `verify_outlook_credentials` skips verification for emails ending in `@example.com` or `.test`.
**Recommendations**:
*   **IMMEDIATELY** enable proper encryption (Fernet) for Outlook passwords.
*   Ensure `ENCRYPTION_KEY` is persistently stored and backed up; otherwise, all encrypted data becomes unreadable on restart/redeploy.

### `form_filler/automation_worker.py`
**Summary**: A worker process that runs the Playwright automation.
**Analysis**:
*   **SQL Injection**: `update_db_status` uses f-string formatting to build SQL queries: `sql = f"UPDATE ... {', '.join(updates)} ..."`. This is highly vulnerable.
*   **Process Management**: Launches a subprocess for the worker. This is fragile and hard to monitor.
*   **Error Handling**: Broad try/except blocks print to stdout/stderr.
**Recommendations**:
*   Rewrite SQL queries to use parameterized inputs (`%s`).
*   Use a proper task queue (Celery/RQ).

### `form_filler/db.py`
**Summary**: Database connection utility.
**Analysis**:
*   **Hardcoded Credentials**: Contains a fallback hardcoded DB user `postgres.uehkqlamchtdzcusqmhi`.
*   **Connection Handling**: Basic `psycopg2` connection. No connection pooling configured, which will lead to performance issues under load.
**Recommendations**:
*   Remove hardcoded user.
*   Implement connection pooling (e.g., `psycopg2.pool.SimpleConnectionPool`).

## 2. Mail Agent

### `mail_agent/gmail_service.py`
**Summary**: Interacts with Gmail API to fetch emails.
**Analysis**:
*   **Auth**: Supports both `token.json` (local) and environment variable `GMAIL_TOKEN_JSON`.
*   **Logic**: Simple scraping of latest email.
*   **Regex**: Uses regex to find links. Robustness depends on email format.

### `mail_agent/groq_service.py`
**Summary**: Uses Groq (LLM) to parse email content and verify form data.
**Analysis**:
*   **Dependency**: specific `llama-3.3-70b-versatile` model. If this model is deprecated, service fails.
*   **Error Handling**: Basic try/except. Returns `None` on failure.

## 3. Frontend (`doc_handle/src/`)

### `doc_handle/src/utils/api.ts`
**Summary**: Axios instance configuration.
**Analysis**:
*   **Hardcoded URL**: Fallback URL is `https://outing-backend-api.azurewebsites.net/api`. This should be purely environment-driven.
*   **Logic**: Contains defensive coding to strip double `/api` prefixes, indicating past configuration issues.

### `doc_handle/src/utils/auth.ts`
**Summary**: Auth helper functions.
**Analysis**:
*   **Storage**: Stores JWT token and user object in `localStorage`. Standard practice for simple apps but vulnerable to XSS.

## 4. Utility Scripts (Root Directory)

**Status Key**:
*   🔴 **Critical Risk** (Contains secrets/dangerous logic)
*   🟡 **Caution** (Deprecated/Messy)
*   🟢 **Safe/Useful**

| File | Status | Analysis |
| :--- | :--- | :--- |
| `check_db_logs.py` | 🔴 | Hardcoded DB connection details. prints sensitive logs to stdout. |
| `debug_env.py` | 🟡 | Prints environment variables to stdout. useful for debug but dangerous in logs. |
| `test_db_connect.py` | 🔴 | Hardcoded DB password and host. |
| `test_payment.py` | 🟡 | Hardcoded test user credentials. Performs real network requests to production URL. |
| `check_queue_status.py` | 🟢 | Harmless check of internal queue size. |
| `create_deploy_zip.py` | 🟢 | Devops utility. |
| `fix_azure_config.py` | 🟡 | Modifies Azure config via CLI. Hardcoded resource group/app names. |
| `generate_stable_key.py` | 🟢 | Generates a key. Safe. |
| `parse_creds.py` | 🟡 | Parses a specific JSON structure. Utility. |
| `setup_payment_local.py` | 🔴 | Hardcoded DB credentials. |
| `test_key.py` | 🟢 | Tests encryption key generation. |
| `update_config.py` | 🟡 | Runs Azure CLI commands with hardcoded image tag. |
| `verify_razorpay_keys.py` | 🟡 | Tests Razorpay connection. Requires env vars. |

## 5. Database Schema

### `database/schema.sql` vs `database/schema_supabase.sql`
**Analysis**:
*   There are two schema files. `schema_supabase.sql` appears to be the "clean reset" version.
*   `schema.sql` contains `IF NOT EXISTS` clauses, suggesting it's for incremental updates.
*   **Inconsistency**: Having two sources of truth is dangerous.
**Recommendations**:
*   Consolidate into a single schema file or use a migration tool (Alembic/Flyway).

## 6. Infrastructure

### `Dockerfile`
**Analysis**:
*   Based on `python:3.11-slim`.
*   Installs system dependencies for Playwright.
*   **Issue**: Runs `playwright install chromium` which is heavy.
*   **Command**: `CMD ["gunicorn", ...]` with 600s timeout. This is extremely long and masks performance issues.

### `startup.sh`
**Analysis**:
*   Simple bash script.
*   **Issue**: Comments say "Playwright is NOT available - Outlook verification is disabled", but Dockerfile installs it. Conflicting information.

## Summary of Critical Actions Required

1.  **Security**: Rotate all keys. Enable Outlook password encryption. Delete utility scripts with hardcoded credentials (`check_db_logs.py`, `test_db_connect.py`, etc.).
2.  **Architecture**: Replace in-memory task queue with Redis.
3.  **Cleanup**: Delete unused/duplicate scripts to reduce attack surface.
