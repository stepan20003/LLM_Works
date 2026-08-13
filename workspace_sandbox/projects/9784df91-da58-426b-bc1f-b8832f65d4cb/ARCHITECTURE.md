# Architecture Specification

```json
{
  "project_name": "auth-service",
  "tech_stack": [
    "Python",
    "FastAPI",
    "PostgreSQL",
    "Docker",
    "pytest",
    "Pydantic",
    "Passlib"
  ],
  "directory_structure": [
    "app/",
    "tests/",
    "Dockerfile",
    "pyproject.toml",
    "requirements.txt"
  ],
  "required_files": [
    {
      "path": "app/__init__.py",
      "description": "Package initializer"
    },
    {
      "path": "app/main.py",
      "description": "FastAPI application entrypoint with routes and middleware"
    },
    {
      "path": "app/auth.py",
      "description": "Authentication logic and models"
    },
    {
      "path": "app/users.py",
      "description": "User models and database operations"
    },
    {
      "path": "tests/test_auth.py",
      "description": "Unit tests for authentication logic"
    },
    {
      "path": "tests/test_users.py",
      "description": "Unit tests for user models and database operations"
    },
    {
      "path": "Dockerfile",
      "description": "Container build configuration"
    },
    {
      "path": "pyproject.toml",
      "description": "Project dependencies and metadata"
    },
    {
      "path": "requirements.txt",
      "description": "Project dependencies"
    },
    {
      "path": "README.md",
      "description": "Project setup and run instructions"
    },
    {
      "path": "models/user.py",
      "description": "User model definition"
    },
    {
      "path": "schemas/user.py",
      "description": "User schema definition"
    },
    {
      "path": "database/db.py",
      "description": "Database connection and operations"
    }
  ],
  "env_variables": [
    "DATABASE_URL",
    "SECRET_KEY",
    "JWT_SECRET_KEY"
  ],
  "run_instructions": "docker-compose up --build"
}
```
