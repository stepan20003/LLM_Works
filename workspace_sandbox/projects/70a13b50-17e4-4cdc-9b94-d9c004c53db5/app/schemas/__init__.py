# Schemas package initializer
from pydantic import BaseModel
from typing import Optional

class BaseSchema(BaseModel):
    class Config:
        orm_mode = True