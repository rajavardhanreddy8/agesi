# Outing Automation Agent 4.0

An intelligent agent that automates the submission of outing permission forms using Playwright, React, and Flask, now with **Full Authentication**.

## Features
- **User Authentication**: Secure Login/Register with Email Verification.
- **Profile Management**: Stores student and parent details securely.
- **Outlook Integration**: Encrypted storage of Outlook credentials for automation.
- **Automated Form Filling**: Playwright agent fills Microsoft Forms automatically.
- **PDF Generation**: Auto-generates permission letters.

## Quick Start
See [docs/SETUP.md](docs/SETUP.md) for detailed installation instructions.

## Architecture
- **Frontend**: Vite + React (Pages: Login, Register, Dashboard)
- **Backend**: Flask + PostgreSQL
- **Automation**: Playwright (Headful mode for reliability)
- **Database**: PostgreSQL (Users, Profiles, History)

## New Directory Structure
- `doc_handle/`: React Frontend (Port 5173)
- `form_filler/`: Flask Backend (Port 5000)
- `database/`: SQL Schema and migrations
- `docs/`: Documentation
