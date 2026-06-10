import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID",     "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
JWT_SECRET           = os.getenv("JWT_SECRET",           "capstone-jwt-secret-2024")
SESSION_SECRET       = os.getenv("SESSION_SECRET",       "capstone-session-2024")
FRONTEND_URL         = os.getenv("FRONTEND_URL",         "http://localhost:8501")
ALGORITHM            = "HS256"


def create_token(user_id: str, email: str, name: str, role: str = None) -> str:
    payload = {
        "sub":   user_id,
        "email": email,
        "name":  name,
        "role":  role,
        "exp":   datetime.utcnow() + timedelta(days=7),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError as e:
        raise HTTPException(status_code=401, detail=str(e))
