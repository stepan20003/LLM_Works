import os

class DatabaseConfig:
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_NAME = os.environ.get('DB_NAME', 'task_management_api')
    DB_USER = os.environ.get('DB_USER', 'task_management_api_user')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'task_management_api_password')
    DB_PORT = os.environ.get('DB_PORT', 5432)