# User schema implementation
from app.schemas import BaseSchema

class UserSchema(BaseSchema):
    id: int
    name: str
    email: str