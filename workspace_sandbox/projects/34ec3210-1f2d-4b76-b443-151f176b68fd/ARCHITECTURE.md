# Architecture Specification

```json
{
  "project_name": "auth-service",
  "tech_stack": [
    "Python",
    "FastAPI",
    "PostgreSQL",
    "Docker",
    "pytest"
  ],
  "directory_structure": [
    "app/",
    "tests/",
    "Dockerfile",
    "pyproject.toml",
    "requirements.txt",
    "README.md"
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
      "description": "User models and database interactions"
    },
    {
      "path": "tests/test_main.py",
      "description": "Unit tests for application endpoints"
    },
    {
      "path": "tests/test_auth.py",
      "description": "Unit tests for authentication logic"
    },
    {
      "path": "tests/test_users.py",
      "description": "Unit tests for user models and database interactions"
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
