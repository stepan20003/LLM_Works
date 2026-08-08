# test_calculator.py
import pytest
from calculator import Calculator

def test_add():
    calculator = Calculator()
    assert calculator.add(5, 3) == 8

def test_subtract():
    calculator = Calculator()
    assert calculator.subtract(5, 3) == 2

def test_multiply():
    calculator = Calculator()
    assert calculator.multiply(5, 3) == 15

def test_divide():
    calculator = Calculator()
    assert calculator.divide(6, 2) == 3

def test_divide_by_zero():
    calculator = Calculator()
    with pytest.raises(ValueError):
        calculator.divide(6, 0)

def test_add_negative_numbers():
    calculator = Calculator()
    assert calculator.add(-5, -3) == -8

def test_subtract_negative_numbers():
    calculator = Calculator()
    assert calculator.subtract(-5, -3) == -2

def test_multiply_negative_numbers():
    calculator = Calculator()
    assert calculator.multiply(-5, -3) == 15

def test_divide_negative_numbers():
    calculator = Calculator()
    assert calculator.divide(-6, 2) == -3