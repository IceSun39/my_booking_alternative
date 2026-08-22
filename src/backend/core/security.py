from datetime import datetime, timedelta, timezone
import os

import jwt
from dotenv import load_dotenv
from fastapi import HTTPException
from pwdlib import PasswordHash
import uuid
import logging

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30
password_hash = PasswordHash.recommended()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return password_hash.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None, refresh: bool = False) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    to_encode.update({'jti': str(uuid.uuid4())})
    to_encode.update({'refresh': refresh})
    encoded_jwt = jwt.encode(payload=to_encode, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    try:
        token_data = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=[ALGORITHM])
        return token_data
    except jwt.ExpiredSignatureError:
        logging.error("Expired token")
        raise HTTPException(
            status_code=401,
            detail="Token expired",
        )
    except jwt.InvalidTokenError:
        logging.error("Invalid token")
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )


