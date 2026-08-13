import pytest
from app.core import calculator
from app.core import settings

def test_calculator_add():
    """Test the add method of the Calculator class."""
    calculator_instance = calculator.Calculator()
    result = calculator_instance.add(5, 10)
    assert result == 15

def test_settings():
    """Test the application settings."""
    assert settings.POSTGRES_USER == "user"
    assert settings.POSTGRES_PASSWORD == "password"
    assert settings.POSTGRES_DB == "db"
    assert settings.POSTGRES_HOST == "localhost"
    assert settings.POSTGRES_PORT == 5432