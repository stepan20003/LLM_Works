import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_root():
    """Test the root endpoint of the API."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Calculator API"}

def test_api_add():
    """Test the add endpoint of the API."""
    response = client.get("/add/5/10")
    assert response.status_code == 200
    assert response.json() == {"result": 15}

def test_api_add_invalid_input():
    """Test the add endpoint with invalid input values."""
    response = client.get("/add/5/abc")
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "value is not a valid integer"