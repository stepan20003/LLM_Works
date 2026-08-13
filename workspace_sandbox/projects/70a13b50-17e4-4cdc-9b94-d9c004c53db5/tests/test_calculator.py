import pytest
from app.core import calculator

def test_calculator_add():
    """Test the add method of the Calculator class."""
    result = calculator.Calculator().add(5, 10)
    assert result == 15

def test_calculator_add_invalid_type():
    """Test the add method with invalid input types."""
    with pytest.raises(TypeError):
        calculator.Calculator().add("five", 10)

def test_calculator_add_invalid_input():
    """Test the add method with invalid input values."""
    with pytest.raises(ValueError):
        calculator.Calculator().add(5, None)