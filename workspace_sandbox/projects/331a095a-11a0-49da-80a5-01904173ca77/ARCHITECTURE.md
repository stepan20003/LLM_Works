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
  "requirements_map": {
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
    ],
    "Registration": [
      "app/api/routes/users.py",
      "app/schemas/user.py"
    ],
    "Login": [
      "app/api/routes/auth.py",
      "app/schemas/auth.py"
    ],
    "Password Recovery": [
      "app/api/routes/auth.py",
      "app/schemas/auth.py"
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
    "requirements/",
    "docker-compose.yml"
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
      "path": "app/core/security.py",
      "description": "Security module for JWT authentication",
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
      "description": "API routes for authentication",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/api/routes/users.py",
      "description": "API routes for user CRUD",
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
      "description": "Schemas for user data",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/schemas/auth.py",
      "description": "Schemas for authentication data",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "tests/__init__.py",
      "description": "Test package initializer",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "tests/test_main.py",
      "description": "Unit tests for application endpoints",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "tests/test_security.py",
      "description": "Unit tests for security module",
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
      "description": "Environment variable configuration example",
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
      "path": "requirements/requirements.txt",
      "description": "Project dependencies",
      "language": "text",
      "is_test": false,
      "is_config": true
    },
    {
      "path": "docker-compose.yml",
      "description": "Container build and deployment configuration",
      "language": "yaml",
      "is_test": false,
      "is_config": true
    },
    {
      "path": "Dockerfile",
      "description": "Container build configuration",
      "language": "dockerfile",
      "is_test": false,
      "is_config": true
    },
    {
      "path": "README.md",
      "description": "Project documentation",
      "language": "markdown",
      "is_test": false,
      "is_config": false
    }
  ],
  "env_variables": [
    "DATABASE_URL",
    "SECRET_KEY"
  ],
  "run_instructions": "docker-compose up"
}
```
