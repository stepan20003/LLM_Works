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
    "docker-compose.yml",
    "Dockerfile"
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
      "description": "Security utilities and JWT authentication",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/core/utils.py",
      "description": "Utility functions",
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
      "description": "Database connection and query utilities",
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
      "path": "app/api/routes/users.py",
      "description": "User routes",
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
      "path": "app/schemas/auth.py",
      "description": "Authentication schema",
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
      "path": "tests/test_auth.py",
      "description": "Unit tests for authentication routes",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "tests/test_users.py",
      "description": "Unit tests for user routes",
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
      "path": "docker-compose.yml",
      "description": "Container orchestration configuration",
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
    }
  ],
  "env_variables": [
    "DATABASE_URL",
    "SECRET_KEY"
  ],
  "run_instructions": "docker-compose up --build"
}
```
