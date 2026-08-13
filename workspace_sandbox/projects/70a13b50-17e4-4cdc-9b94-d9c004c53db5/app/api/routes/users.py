# User CRUD routes implementation
from fastapi import APIRouter, Depends, HTTPException
from app.core import database, settings
from app.schemas.user import UserSchema
from app.core.calculator import Calculator

router = APIRouter()

@router.get("/users/")
async def read_users(db: database.SessionLocal = Depends(database.get_db)):
    return db.query(UserSchema).all()

@router.post("/users/")
async def create_user(user: UserSchema, db: database.SessionLocal = Depends(database.get_db)):
    db_user = UserSchema(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/users/{user_id}")
async def read_user(user_id: int, db: database.SessionLocal = Depends(database.get_db)):
    db_user = db.query(UserSchema).filter(UserSchema.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/users/{user_id}")
async def update_user(user_id: int, user: UserSchema, db: database.SessionLocal = Depends(database.get_db)):
    db_user = db.query(UserSchema).filter(UserSchema.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.__dict__.update(user.dict())
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, db: database.SessionLocal = Depends(database.get_db)):
    db_user = db.query(UserSchema).filter(UserSchema.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return {"message": "User deleted successfully"}