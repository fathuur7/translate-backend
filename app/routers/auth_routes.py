from fastapi import APIRouter, Request, Depends
from app.controllers.auth_controller import AuthController
from app.middleware.auth_middleware import require_auth, require_verified_email

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])

auth = AuthController()

# =======================
# PUBLIC ROUTES
# =======================

@auth_router.get("/google")
async def google_login():
    return await auth.google_login()

@auth_router.get("/google/callback")
async def google_callback(request: Request):
    return await auth.google_callback(request)

# =======================
# PROTECTED ROUTES
# =======================

@auth_router.post("/logout")
async def logout(user=Depends(require_auth)):
    return await auth.logout(user)

@auth_router.get("/me")
async def get_current_user(user=Depends(require_auth)):
    return await auth.get_current_user(user)

@auth_router.get("/me/verified")
async def get_verified_user(user=Depends(require_verified_email)):
    return {"message": "Email verified!", "user": user}
