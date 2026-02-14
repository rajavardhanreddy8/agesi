# Codebase Audit Report

## Executive Summary
The "Campus Outing Automation System" is a full-stack application designed to automate student outing requests. It features a React frontend, a Flask backend, and integrations with Microsoft Forms, Azure Blob Storage, Gmail, and Razorpay.

While the core functionality for form filling and PDF generation appears implemented, the project suffers from significant security vulnerabilities, architectural gaps, and maintenance issues.

## 1. Security Vulnerabilities (High Criticality)

*   **Raw Password Storage**: `auth_system_v2.py` explicitly disables encryption for Outlook passwords (`encrypt_outlook_password` returns the raw password). This is a severe security risk. If the database is compromised, all user email credentials are exposed.
*   **Hardcoded Secrets**: `api.py` and `auth_system_v2.py` contain fallback/default secret keys (e.g., `JWT_SECRET = 'your-secret-key-change-this'`, `ADMIN_PASSWORD = 'rama:123'`). While environment variables are preferred, these defaults are dangerous if not overridden.
*   **SQL Injection Risk**: `automation_worker.py` uses string formatting for SQL queries (`sql = f"UPDATE ..."`). This is vulnerable to SQL injection. It should strictly use parameterized queries.
*   **Debug Endpoints**: The root directory contains many ad-hoc debug scripts (`check_db_logs.py`, `read_env.py`) that might expose sensitive environment data if deployed or accessible via a misconfigured server.

## 2. Architecture & Design Gaps

*   **In-Memory State**: `api.py` uses a global `automation_tasks` dictionary and a Python `queue.Queue` for task management. This is not scalable and will lose all state if the application restarts or scales to multiple worker instances (e.g., in a containerized environment).
    *   *Recommendation*: Use Redis or a database table for the task queue.
*   **Circular/Complex Imports**: The project has a complex import structure requiring `sys.path.append` hacks in `automation_worker.py` and `api.py` to make imports work.
*   **Blocking Operations**: The `automation_worker` runs as a thread within the Flask app process. Heavy browser automation (Playwright) can impact API responsiveness. It should ideally be a separate worker service (e.g., Celery).

## 3. Code Quality & Maintainability

*   **Duplicate Code**:
    *   Database connection logic is repeated in `db.py` and `api.py` (though partially refactored in recent changes).
    *   Environment variable loading logic is duplicated across many files (`api.py`, `automation_worker.py`, `db.py`).
*   **Lack of Error Handling**: `automation_worker.py` has broad `try/except Exception` blocks that catch everything but might mask critical system failures.
*   **Hardcoded Values**:
    *   `auth_system_v2.py` has a hardcoded timeout of `30000` ms for Playwright.
    *   `api.py` hardcodes the IP `127.0.0.1` for task creation.

## 4. Frontend & User Experience

*   **Frontend Integration**: The frontend exists in `doc_handle/` but there is no clear build/deploy pipeline linking it to the Flask backend (except for `app_bundle.js` in the root, which seems to be an artifact).
*   **Validation**: The frontend code was not deeply audited, but the backend `api.py` does basic validation. Robust validation should exist on both ends.

## 5. Infrastructure & Deployment

*   **Dockerfile**: The Dockerfile installs dependencies but runs Gunicorn with a timeout of 600s, which is very high.
*   **Missing CI/CD**: There are GitHub workflow files, but they seem to deploy to Azure. The project lacks a unified build process that handles both frontend and backend assets.
*   **Database**: The schema files (`database/schema.sql` vs `database/schema_supabase.sql`) show inconsistency. It's unclear which is the source of truth.

## Recommendations

1.  **Security First**: Immediately implement proper encryption for Outlook passwords. Remove all hardcoded secrets and ensure they are only loaded from `.env`.
2.  **Refactor Worker**: Move the automation worker to a robust task queue system (like Celery with Redis) to ensure reliability and scalability.
3.  **Clean Up**: Remove the dozens of root-level utility scripts (`check_*.py`, `test_*.py`) that clutter the project and pose security risks.
4.  **Standardize DB**: Choose one schema file as the source of truth and use migration tools (like Alembic) to manage database changes.
5.  **Fix SQL Injection**: Rewrite the `update_db_status` function in `automation_worker.py` to use parameterized queries.

## Recent Fixes (Implemented)

*   **Dependencies**: Added `requirements.txt` to lock python dependencies.
*   **Documentation**: Added `README.md` to guide setup.
*   **Testing**: Added `tests/` directory with basic API tests.
*   **Imports**: Refactored `form_filler/api.py` to fix relative import issues.
