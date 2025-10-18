from jose import jwt, JWTError
from fastapi import Request, HTTPException, status, Depends
from datetime import datetime, timezone
import os


# Ganti dengan secret key kamu sendiri
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"


def decode_jwt_token(token: str):
    """Decode JWT token dan kembalikan payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Cek expired
        exp = payload.get("exp")
        if exp and datetime.now(timezone.utc).timestamp() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


async def require_auth(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # <--- ini yang dikirim ke controller
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def require_verified_email(user=Depends(require_auth)):
    """Wajib email verified"""
    if not user.get("email_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email to access this resource"
        )
    return user


async def optional_auth(request: Request):
    """Tidak wajib login"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]
    try:
        user = decode_jwt_token(token)
        return user
    except Exception:
        return None
