"""
API routes package initializer.
"""
from fastapi import APIRouter
from app.api.routes.calculator import router as calculator_router

router = APIRouter()
router.include_router(calculator_router)