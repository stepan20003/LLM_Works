# Architecture Specification

```json
{
  "project_name": "calculator",
  "tech_stack": [
    "Python",
    "FastAPI",
    "PostgreSQL",
    "Docker",
    "pytest"
  ],
  "requirements_map": {
    "Calculator functionality": [
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
    "config/",
    "docker/"
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
      "description": "Calculator functionality",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/core/security.py",
      "description": "Security and authentication",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/db/__init__.py",
      "description": "Database package initializer",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/db/database.py",
      "description": "Database connection and operations",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/db/models.py",
      "description": "Database models",
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
      "path": "app/api/routes/auth.py",
      "description": "Authentication routes",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/api/routes/calculator.py",
      "description": "Calculator routes",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/api/routes/users.py",
      "description": "User CRUD routes",
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
      "path": "tests/test_core.py",
      "description": "Unit tests for core functionality",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "tests/test_calculator.py",
      "description": "Unit tests for calculator functionality",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "tests/test_api.py",
      "description": "Unit tests for API routes",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "docs/README.md",
      "description": "Project documentation",
      "language": "markdown",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "config/.env.example",
      "description": "Environment variables example",
      "language": "bash",
      "is_test": false,
      "is_config": true
    },
    {
      "path": "config/pyproject.toml",
      "description": "Project dependencies and metadata",
      "language": "toml",
      "is_test": false,
      "is_config": true
    },
    {
      "path": "docker/Dockerfile",
      "description": "Container build configuration",
      "language": "dockerfile",
      "is_test": false,
      "is_config": true
    },
    {
      "path": "docker/docker-compose.yml",
      "description": "Container orchestration configuration",
      "language": "yml",
      "is_test": false,
      "is_config": true
    }
  ],
  "env_variables": [
    "DATABASE_URL",
    "SECRET_KEY"
  ],
  "run_instructions": "Command to launch and test the project: docker-compose up"
}
```
