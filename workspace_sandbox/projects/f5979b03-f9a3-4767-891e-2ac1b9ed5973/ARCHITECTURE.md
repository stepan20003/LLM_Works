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
  "requirements_map": {
    "Calculator module": [
      "app/core/calculator.py",
      "app/api/routes/calculator.py"
    ],
    "JWT authentication": [
      "app/core/security.py",
      "app/api/routes/auth.py"
    ],
    "PostgreSQL database": [
      "app/db/database.py",
      "app/db/models.py"
    ],
    "User CRUD": [
      "app/api/routes/users.py",
      "app/schemas/user.py"
    ]
  },
  "directory_structure": [
    "app/",
    "app/core/",
    "app/db/",
    "app/api/",
    "app/api/routes/",
    "app/schemas/",
    "tests/",
    "docs/",
    "requirements.txt",
    ".env.example"
  ],
  "required_files": [
    {
      "path": "app/__init__.py",
      "description": "Package initializer",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/main.py",
      "description": "FastAPI application entrypoint with routes and middleware",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/core/__init__.py",
      "description": "Core package initializer",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/core/calculator.py",
      "description": "Calculator module with arithmetic operations",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/core/security.py",
      "description": "Security module with JWT authentication",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/api/__init__.py",
      "description": "API package initializer",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/api/routes/__init__.py",
      "description": "API routes package initializer",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/api/routes/calculator.py",
      "description": "Calculator API routes",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/api/routes/users.py",
      "description": "User API routes",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/schemas/__init__.py",
      "description": "Schemas package initializer",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/schemas/user.py",
      "description": "User schema",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "tests/__init__.py",
      "description": "Tests package initializer",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "tests/test_calculator.py",
      "description": "Calculator module unit tests",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "tests/test_api.py",
      "description": "API routes unit tests",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "Dockerfile",
      "description": "Container build configuration",
      "language": "dockerfile",
      "is_test": false,
      "is_config": true
    },
    {
      "path": "docker-compose.yml",
      "description": "Container orchestration configuration",
      "language": "yml",
      "is_test": false,
      "is_config": true
    },
    {
      "path": "requirements.txt",
      "description": "Project dependencies",
      "language": "txt",
      "is_test": false,
      "is_config": true
    },
    {
      "path": ".env.example",
      "description": "Environment variables example",
      "language": "txt",
      "is_test": false,
      "is_config": true
    },
    {
      "path": "pyproject.toml",
      "description": "Project metadata and dependencies",
      "language": "toml",
      "is_test": false,
      "is_config": true
    },
    {
      "path": "README.md",
      "description": "Project setup and run instructions",
      "language": "markdown",
      "is_test": false,
      "is_config": false
    }
  ],
  "env_variables": [
    "DATABASE_URL",
    "SECRET_KEY"
  ],
  "run_instructions": "Command to launch and test the project: `docker-compose up`"
}
```
