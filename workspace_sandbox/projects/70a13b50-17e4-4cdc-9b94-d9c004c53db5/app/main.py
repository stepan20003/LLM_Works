from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core import calculator
from app.core import database
from app.core import settings

app = FastAPI(
    title="Calculator API",
    description="API for performing calculator operations",
    version="1.0.0",
)

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

@app.get("/add/{num1}/{num2}")
async def add(num1: float, num2: float):
    return {"result": calculator.add(num1, num2)}