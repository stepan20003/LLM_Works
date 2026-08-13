"""
Security and authentication implementation.
"""
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from app.core.settings import Settings

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Security:
    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Returns the hashed password.

        Args:
            password (str): The password to hash.

        Returns:
            str: The hashed password.
        """
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verifies the password.

        Args:
            plain_password (str): The plain password.
            hashed_password (str): The hashed password.

        Returns:
            bool: True if the password is valid, False otherwise.
        """
        return Security.get_password_hash(plain_password) == hashed_password