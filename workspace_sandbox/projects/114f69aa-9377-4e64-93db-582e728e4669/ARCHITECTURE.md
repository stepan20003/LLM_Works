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
      "app/schemas/user.py"
    ],
    "Password Recovery": [
      "app/api/routes/auth.py",
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
    "config/",
    "docs/",
    "requirements/",
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
      "description": "Package initializer",
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
      "path": "app/db/__init__.py",
      "description": "Package initializer",
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
      "description": "Database models for users and authentication",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/api/__init__.py",
      "description": "Package initializer",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/api/routes/__init__.py",
      "description": "Package initializer",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/api/routes/auth.py",
      "description": "Authentication routes (login, password recovery)",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/api/routes/users.py",
      "description": "User CRUD routes (registration, user management)",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/schemas/__init__.py",
      "description": "Package initializer",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/schemas/user.py",
      "description": "User schema and validation",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "tests/__init__.py",
      "description": "Package initializer",
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
      "description": "Unit tests for security utilities",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "tests/test_database.py",
      "description": "Unit tests for database connection and query utilities",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "tests/test_routes.py",
      "description": "Unit tests for authentication and user CRUD routes",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "config/__init__.py",
      "description": "Package initializer",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "config/settings.py",
      "description": "Application settings and configuration",
      "language": "python",
      "is_test": false,
      "is_config": true
    },
    {
      "path": "config/secret.py",
      "description": "Secrets and environment variables",
      "language": "python",
      "is_test": false,
      "is_config": true
    },
    {
      "path": "config/database.py",
      "description": "Database connection settings",
      "language": "python",
      "is_test": false,
      "is_config": true
    },
    {
      "path": "requirements.txt",
      "description": "Project dependencies",
      "language": "text",
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
      "path": "docker-compose.yml",
      "description": "Container orchestration and database setup",
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
  "run_instructions": "docker-compose up --build"
}
```
