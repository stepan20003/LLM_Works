# Architecture Specification

```json
{
  "project_name": "ecommerce-zip-test",
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
    "Product CRUD": [
      "app/api/routes/products.py",
      "app/schemas/product.py"
    ],
    "Order CRUD": [
      "app/api/routes/orders.py",
      "app/schemas/order.py"
    ],
    "Payment Gateway": [
      "app/api/routes/payments.py",
      "app/schemas/payment.py"
    ],
    "Zip Code Validation": [
      "app/api/routes/zipcodes.py",
      "app/schemas/zipcode.py"
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
      "path": "app/db/__init__.py",
      "description": "Database package initializer",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/db/database.py",
      "description": "Database connection and query module",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/db/models.py",
      "description": "Database models for users, products, and orders",
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
      "description": "API route for JWT authentication",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/api/routes/users.py",
      "description": "API route for user CRUD operations",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/api/routes/products.py",
      "description": "API route for product CRUD operations",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/api/routes/orders.py",
      "description": "API route for order CRUD operations",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/api/routes/payments.py",
      "description": "API route for payment gateway",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/api/routes/zipcodes.py",
      "description": "API route for zip code validation",
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
      "description": "Schema for user data",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/schemas/product.py",
      "description": "Schema for product data",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/schemas/order.py",
      "description": "Schema for order data",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/schemas/payment.py",
      "description": "Schema for payment data",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/schemas/zipcode.py",
      "description": "Schema for zip code data",
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
      "path": "tests/test_auth.py",
      "description": "Unit tests for JWT authentication",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "tests/test_users.py",
      "description": "Unit tests for user CRUD operations",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "tests/test_products.py",
      "description": "Unit tests for product CRUD operations",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "tests/test_orders.py",
      "description": "Unit tests for order CRUD operations",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "tests/test_payments.py",
      "description": "Unit tests for payment gateway",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "tests/test_zipcodes.py",
      "description": "Unit tests for zip code validation",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "config/__init__.py",
      "description": "Config package initializer",
      "language": "python",
      "is_test": false,
      "is_config": true
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
      "path": "config/requirements.txt",
      "description": "Project dependencies",
      "language": "text",
      "is_test": false,
      "is_config": true
    },
    {
      "path": "docker-compose.yml",
      "description": "Container build and deployment configuration",
      "language": "yml",
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
    "SECRET_KEY",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB"
  ],
  "run_instructions": "docker-compose up --build"
}
```
