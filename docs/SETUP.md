# Setup Guide - Outing Automation Authentication

## 1. Prerequisites
- **PostgreSQL**: Ensure PostgreSQL is installed and running on port 5432.
- **Python 3.8+**: With `pip`.
- **Node.js 18+**: With `npm`.

## 2. Database Setup (CRITICAL)
⚠️ **You must run this manually as `psql` was not found in the system path.**

1. Open your terminal or a tool like Logstash/pgAdmin.
2. Connect to your PostgreSQL server.
3. Create the database `outing_automation` (if not exists).
4. Run the schema file located at `database/schema.sql`.

Command line example (if psql is installed somewhere):
```bash
psql -U postgres -f database/schema.sql
```

## 3. Backend Setup (`form_filler/`)
1. Navigate to `form_filler/` directory.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Update `.env` file:
   - Set `DB_PASSWORD` to your Postgres password.
   - Set `ENCRYPTION_KEY` (Generate one using `cryptography.fernet.Fernet.generate_key()`).
   - Set `SMTP_PASSWORD` with your Gmail App Password.

4. Run the server:
   ```bash
   python api.py
   ```
   Server runs on http://localhost:5000.

## 4. Frontend Setup (`campusouting/`)
1. Navigate to `campusouting/` directory.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   App runs on http://localhost:5173 (usually).

## 5. Usage
1. Go to http://localhost:5173/register
2. Sign up with your `@woxsen.edu.in` email and Outlook password.
3. Check your email (simulated in logs if SMTP fails) for verification link.
4. Login.
5. Go to Dashboard and try submitting a form.
