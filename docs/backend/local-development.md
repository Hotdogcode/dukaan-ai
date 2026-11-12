# Local Development Guide

## Overview
This guide instructs backend developers on how to configure, run, test, and debug the DukaanAI backend services locally.

## Prerequisites
- Python 3.12 or higher.
- Docker & Docker Compose (for local PostgreSQL 16).
- Git.

## Environment Setup

### 1. Clone Repository and Create Virtual Environment
```bash
git clone https://github.com/dukaanai/dukaanai.git
cd dukaanai/backend
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Key variables to inspect:
- `ENVIRONMENT=development`
- `DATABASE_URL=postgresql+psycopg://dukaanai:dukaanai_dev_password@localhost:5432/dukaanai_db`
- `JWT_SECRET_KEY=dev-secret-key-change-in-production-min-32-chars`
- `OTP_PEPPER=dev-otp-pepper-change-in-production-min-32-chars`
- `OTP_DEV_MODE=True` (logs simulated OTP dispatch without needing SMS gateway credentials)

## Running Infrastructure via Docker Compose
To start local PostgreSQL 16:
```bash
cd infrastructure/docker
docker compose up -d postgres
```

## Running Database Migrations
Apply Alembic migrations to build all 43 tables and RLS policies:
```bash
cd backend
alembic upgrade head
```

## Running the Backend API Server
Start the development server with live reload:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Interactive Swagger UI: `http://localhost:8000/docs`
- ReDoc Documentation: `http://localhost:8000/redoc`
- OpenAPI JSON Schema: `http://localhost:8000/openapi.json`
- Liveness Check: `http://localhost:8000/health`
- Readiness Check: `http://localhost:8000/health/ready`

## Running Automated Tests
Run the entire test suite using pytest:
```bash
cd backend
pytest -v
```
To run tests with specific markers or directories:
```bash
# Unit tests
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# Security & multi-tenant isolation tests
pytest tests/security -v
```

## Code Quality & Linting
Format and check the codebase using Ruff:
```bash
ruff check .
ruff format .
```
