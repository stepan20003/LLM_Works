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
    "User registration and login": [
      "app/core/security.py",
      "app/api/routes/auth.py"
    ],
    "Product CRUD": [
      "app/api/routes/products.py",
      "app/schemas/product.py"
    ],
    "Order management": [
      "app/api/routes/orders.py",
      "app/schemas/order.py"
    ],
    "Payment gateway integration": [
      "app/api/routes/payments.py",
      "app/schemas/payment.py"
    ],
    "Database connection": [
      "app/db/database.py",
      "app/db/models.py"
    ],
    "Zip code validation": [
      "app/core/utils.py",
      "app/api/routes/checkout.py"
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
      "description": "User authentication and authorization",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/core/utils.py",
      "description": "Utility functions for zip code validation",
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
      "path": "app/api/routes/products.py",
      "description": "Product CRUD routes",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/api/routes/orders.py",
      "description": "Order management routes",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/api/routes/payments.py",
      "description": "Payment gateway integration routes",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/api/routes/checkout.py",
      "description": "Checkout routes with zip code validation",
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
      "path": "app/schemas/product.py",
      "description": "Product schema",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/schemas/order.py",
      "description": "Order schema",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/schemas/payment.py",
      "description": "Payment schema",
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
      "path": "tests/test_products.py",
      "description": "Unit tests for product CRUD routes",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "tests/test_orders.py",
      "description": "Unit tests for order management routes",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "tests/test_payments.py",
      "description": "Unit tests for payment gateway integration routes",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "tests/test_checkout.py",
      "description": "Unit tests for checkout routes with zip code validation",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "config/__init__.py",
      "description": "Config package initializer",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "config/.env.example",
      "description": "Environment variable configuration file",
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
