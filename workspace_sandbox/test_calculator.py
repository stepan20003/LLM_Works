# tests/test_vector.py
import pytest
from calculator import Vector  # Assuming the Vector class is in a calculator module

def test_vector_init():
    v = Vector(2, 3)
    assert v.x == 2
    assert v.y == 3

def test_vector_add():
    v1 = Vector(2, 3)
    v2 = Vector(4, 5)
    result = v1 + v2
    assert result.x == 6
    assert result.y == 8

def test_vector_add_invalid_type():
    v = Vector(2, 3)
    with pytest.raises(TypeError):
        v + 5

def test_vector_str():
    v = Vector(2, 3)
    assert str(v) == "Vector(2, 3)"