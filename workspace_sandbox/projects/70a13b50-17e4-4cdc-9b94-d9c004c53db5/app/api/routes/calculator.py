"""
Calculator operations routes implementation.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from app.core.calculator import Calculator
from app.core.security import Security, oauth2_scheme
from app.core.settings import Settings

router = APIRouter()

class CalculatorRequest(BaseModel):
    num1: float
    num2: float

@router.post("/add")
async def add(num1: float, num2: float):
    """
    Returns the sum of two numbers.

    Args:
        num1 (float): The first number.
        num2 (float): The second number.

    Returns:
        float: The sum of num1 and num2.
    """
    return Calculator.add(num1, num2)

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Returns the access token.

    Args:
        form_data (OAuth2PasswordRequestForm): The form data.

    Returns:
        Token: The access token.
    """
    # For demonstration purposes, we will return a hardcoded token
    # In a real application, you should replace this with a proper authentication mechanism
    return {"access_token": "token", "token_type": "bearer"}