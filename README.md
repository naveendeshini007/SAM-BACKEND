# SAM FastAPI
A modern, scalable, and high-performance backend API leveraging FastAPI for rapid development, asynchronous support, and automatic documentation.

#  FastAPI + Pydantic + Starlette + Uvicorn + SQLAlchemy
A high-performance, asynchronous Python backend stack designed for modern web applications.

# Tech Stack
- **FastAPI**[https://fastapi.tiangolo.com/]: Lightweight, fast (async) web framework for building APIs with automatic docs.
- **Pydantic**[https://docs.pydantic.dev/latest/]: Data validation and settings management using Python type annotations.
- **Starlette**[https://www.starlette.io/]: ASGI toolkit that powers FastAPI with support for WebSockets, middleware, and more.
- **Uvicorn**[https://www.uvicorn.org/]: Ultra-fast ASGI server for running your app in development or production.
- **SQLAlchemy**[https://www.sqlalchemy.org/]: The Python ORM for interacting with relational databases (async-ready).

This stack provides a solid foundation for building scalable, type-safe, and maintainable backend services.

# Getting Started
## 1. Clone the Repository
```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
```
## 2. Create and Activate Virtul Environment
- **create**: python3 -m venv .venv
- **activate**: source .venv/bin/activate
 
## 3. Install Dependencies
  pip install -r requirements.txt
 
## 4. export Data Base URL
  export DATABASE_URL="postgresql+asyncpg:://<username>:<password>@<host>:<port>/<your_db>"

  or Keep the following in the .env file 
  DATABASE_URL="postgresql+asyncpg:://<username>:<password>@<host>:<port>/<your_db>"
 
## 5. Run Server 
- **base**:uvicorn.app.main:app
- **reload**:uvicorn app.main:app --reload 
- **custom port**:uvicorn app.main:app --reload --port 8080
## 6. Unit Testing
Unit tests are written using the `pytest` framework.

- **run all tests**: `pytest`
- **run a specific test file**: `pytest tests/unit/services/test_grantor_rank_service.py`
- **run a specific test function**: `pytest -k "test_grantor_ranking_logic"`
- **show print and logs in output**: `pytest -s`
- **run with pytest coverage**:`pytest --cov=app`
- **run with coverage (terminal)**: `pytest --cov=app --cov-report=term`
- **run with coverage (show missing lines)**: `pytest --cov=app --cov-report=term-missing`
- **generate HTML coverage report**: `pytest --cov=app --cov-report=html`
- **run only unit tests directory**: `pytest tests/unit/`
- **stop after first failure**: `pytest --maxfail=1`
- **suppress warnings**: `pytest --disable-warnings`
- **require minimum 80% coverage**: `pytest --cov=app --cov-fail-under=80`
- **run by marker (e.g., slow)**: `pytest -m slow`
- **generate HTML test result report**: `pytest --html=tests/coverage_reports/pytest_report.html --self-contained-html`
-
Note: Can run by python main.py but not recommended


# Manual first admin setup
# To generate a bcrypt hash locally (python):
python - <<'PY'
from passlib.context import CryptContext
pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')
print(pwd.hash('tempswrd'))
PY

# inside psql, run (replace values):
INSERT INTO admins (admin_id, username, email, password_hash, full_name, must_change_password, is_active)
VALUES (gen_random_uuid(), 'admin', 'admin@example.com', '<bcrypt-hash>', 'Administrator', true, true);


