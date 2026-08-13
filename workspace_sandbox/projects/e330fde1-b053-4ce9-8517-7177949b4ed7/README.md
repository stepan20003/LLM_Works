# Project Overview

> **Project Structure**
```bash
project/
app/
__init__.py
main.py
models/
__init__.py
user.py
schemas/
__init__.py
user.py
database/
__init__.py
__init__.py
core.py
auth.py
crud.py
routes/
__init__.py
auth.py
user.py
tests/
__init__.py
test_auth.py
test_user.py
main.py
requirements.txt
docker-compose.yml
Dockerfile
```

**`requirements.txt`**
```makefile
fastapi
uvicorn
sqlalchemy
psycopg2-binary
pyjwt
pytest
pytest-cov
pytest-fastapi
```

**`docker-compose.yml`**
```yml
version: '3'

services:
  

## Original Request
Build a production-ready FastAPI REST API with JWT authentication, PostgreSQL schema, user CRUD endpoints, unit test suite, and OpenAPI documentation.

## Quick Start / Run Instructions
```bash
# 1. Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Run test suite
pytest

# 3. Run application
python main.py
```

## Generated Artifacts & Structure
- `REQUIREMENTS.md`: Detailed functional requirements & acceptance criteria
- `ARCHITECTURE.md`: System design and component layout
- `TEST_REPORT.md`: Automated test execution findings
- `PROJECT_REPORT.md`: Comprehensive executive project report
- `CHANGELOG.md`: Full version history and iteration log
