# Architecture Specification

```json
{
  "project_name": "simple-calculator",
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
    "requirements.txt"
  ],
  "required_files": [
    {
      "path": "app/__init__.py",
      "description": "Package initializer"
    },
    {
      "path": "app/calculator.py",
      "description": "Calculator module with basic arithmetic operations"
    },
    {
      "path": "app/main.py",
      "description": "FastAPI application entrypoint with calculator API"
    },
    {
      "path": "tests/test_calculator.py",
      "description": "Unit tests for calculator module"
    },
    {
      "path": "tests/test_main.py",
      "description": "Unit tests for application endpoints"
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
    "SECRET_KEY"
  ],
  "run_instructions": "docker-compose up --build"
}
```
