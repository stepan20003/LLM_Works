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
    "Build REST API": [
      "app/api/routes/build.py",
      "app/schemas/build.py"
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
      "description": "JWT authentication implementation",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/core/security.py",
      "description": "JWT authentication implementation",
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
      "path": "app/api/routes/users.py",
      "description": "API user CRUD routes",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/api/routes/build.py",
      "description": "API build CRUD routes",
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
      "path": "app/schemas/build.py",
      "description": "Build schema",
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
      "path": "tests/test_main.py",
      "description": "Unit tests for application endpoints",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "tests/test_users.py",
      "description": "Unit tests for user CRUD routes",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "tests/test_build.py",
      "description": "Unit tests for build CRUD routes",
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
  "run_instructions": "docker-compose up --build"
}
```
