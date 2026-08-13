"""
API package initializer.
"""
from fastapi import APIRouter
from app.api.routes import calculator
from app.core.security import oauth2_scheme

api_router = APIRouter()