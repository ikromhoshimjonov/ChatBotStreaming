from datetime import datetime, timedelta, timezone
from os import getenv

import jwt
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from pwdlib import PasswordHash

load_dotenv()
SECRET_KEY = getenv("SECRET_KEY")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
security_scheme = HTTPBearer(auto_error=False)
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

password_hash = PasswordHash.recommended()

def create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_access_token(username: str) -> str:
    return create_token(
        data={"sub": username, "token_type": "access"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

def create_refresh_token(username: str) -> str:
    return create_token(
        data={"sub": username, "token_type": "refresh"},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )