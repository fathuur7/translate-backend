from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from sqlalchemy.exc import SQLAlchemyError
from jose import jwt, JWTError
import httpx
import os
from datetime import datetime, timedelta

from app.config.db import get_db
from app.models.User import User

class AuthController:
    def __init__(self):
        self.router = APIRouter(prefix="/api/auth", tags=["Auth"])

        # --- ENVIRONMENT VARIABLES ---
        self.GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
        self.GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
        self.GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
        self.FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8080")

        # JWT
        self.JWT_SECRET = os.getenv("JWT_SECRET")
        self.JWT_ALGORITHM = "HS256"
        self.JWT_EXPIRE_MINUTES = 60 * 24  # 1 hari

        # REGISTER ROUTES
        self.router.get("/google")(self.google_login)
        self.router.get("/google/callback")(self.google_callback)
        self.router.post("/logout")(self.logout)
        self.router.get("/me")(self.get_current_user)

    # =====================================================
    # GOOGLE LOGIN
    # =====================================================
    async def google_login(self):
        google_auth_url = (
            "https://accounts.google.com/o/oauth2/v2/auth"
            "?response_type=code"
            f"&client_id={self.GOOGLE_CLIENT_ID}"
            f"&redirect_uri={self.GOOGLE_REDIRECT_URI}"
            "&scope=openid%20email%20profile"
            "&access_type=offline"
            "&prompt=consent"
        )
        return RedirectResponse(url=google_auth_url)

    # =====================================================
    # GOOGLE CALLBACK (EXCHANGE TOKEN)
    # =====================================================
    async def google_callback(self, request: Request):
        try:
            code = request.query_params.get("code")
            if not code:
                return RedirectResponse(f"{self.FRONTEND_URL}/login?error=no_code")

            token_url = "https://oauth2.googleapis.com/token"
            data = {
                "code": code,
                "client_id": self.GOOGLE_CLIENT_ID,
                "client_secret": self.GOOGLE_CLIENT_SECRET,
                "redirect_uri": self.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            }

            async with httpx.AsyncClient() as client:
                token_response = await client.post(token_url, data=data)
                token_json = token_response.json()

            if "error" in token_json:
                return RedirectResponse(f"{self.FRONTEND_URL}/login?error={token_json['error']}")

            # --- VERIFY GOOGLE TOKEN ---
            idinfo = id_token.verify_oauth2_token(
                token_json["id_token"],
                grequests.Request(),
                self.GOOGLE_CLIENT_ID
            )

            user_data = {
                "id": idinfo.get("sub"),
                "email": idinfo["email"],
                "name": idinfo.get("name"),
                "picture": idinfo.get("picture"),
                "email_verified": idinfo.get("email_verified", False),
            }

            # --- SIMPAN KE DATABASE ---
            db = next(get_db())
            try:
                existing_user = db.query(User).filter(User.email == user_data["email"]).first()
                if not existing_user:
                    new_user = User(**user_data)
                    db.add(new_user)
                    db.commit()
                else:
                    existing_user.name = user_data["name"]
                    existing_user.picture = user_data["picture"]
                    existing_user.email_verified = user_data["email_verified"]
                    db.commit()
            except SQLAlchemyError as e:
                db.rollback()
                print(f"❌ Database error: {e}")
            finally:
                db.close()

            # --- BUAT JWT TOKEN ---
            payload = {
                "sub": user_data["email"],
                "name": user_data["name"],
                "picture": user_data["picture"],
                "email_verified": user_data["email_verified"],
                "exp": datetime.utcnow() + timedelta(minutes=self.JWT_EXPIRE_MINUTES),
            }
            jwt_token = jwt.encode(payload, self.JWT_SECRET, algorithm=self.JWT_ALGORITHM)

            # Redirect ke frontend dengan token di URL
            return RedirectResponse(f"{self.FRONTEND_URL}/auth/callback?token={jwt_token}")

        except Exception as e:
            print(f"⚠️ Error: {e}")
            return RedirectResponse(f"{self.FRONTEND_URL}/login?error=server_error")

    # =====================================================
    # GET CURRENT USER (dari JWT payload, bukan DB)
    # =====================================================
    async def get_current_user(self, user: dict):
        """
        user: dict dari middleware (JWT payload)
        Tidak perlu query DB lagi karena data sudah ada di JWT
        """
        try:
            return JSONResponse({
                "success": True,
                "user": {
                    "email": user.get("sub"),  # sub = email
                    "name": user.get("name"),
                    "picture": user.get("picture"),
                    "email_verified": user.get("email_verified", False)
                }
            })
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})

    # =====================================================
    # LOGOUT (FRONTEND ONLY)
    # =====================================================
    async def logout(self, user: dict):
        """
        user: dict dari middleware (opsional, hanya untuk validasi)
        """
        return JSONResponse({
            "success": True, 
            "message": "Token cleared on client side",
            "user_email": user.get("sub")  # Opsional: konfirmasi siapa yang logout
        })