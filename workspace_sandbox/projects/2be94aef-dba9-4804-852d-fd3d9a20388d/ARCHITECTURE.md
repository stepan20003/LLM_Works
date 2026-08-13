# Architecture Specification

```json
{
  "project_name": "build-rest-api",
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
      "path": "app/models.py",
      "description": "Database models for API data"
    },
    {
      "path": "app/routes.py",
      "description": "API endpoint definitions"
    },
    {
      "path": "app/services.py",
      "description": "Business logic for API operations"
    },
    {
      "path": "tests/test_main.py",
      "description": "Unit tests for application endpoints"
    },
    {
      "path": "tests/test_models.py",
      "description": "Unit tests for database models"
    },
    {
      "path": "tests/test_routes.py",
      "description": "Unit tests for API endpoint definitions"
    },
    {
      "path": "tests/test_services.py",
      "description": "Unit tests for business logic"
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
      "description": "External dependencies for the project"
    },
    {
      "path": "README.md",
      "description": "Project setup and run instructions"
    }
  ],
  "env_variables": [
    "DATABASE_URL",
    "SECRET_KEY",
    "API_PREFIX"
  ],
  "run_instructions": "docker-compose up --build"
}
```
