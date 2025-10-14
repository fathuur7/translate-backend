from fastapi import APIRouter
from app.controllers.auth_controller import AuthController
from app.middleware.auth_middleware import require_auth

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])

# Public routes
@auth_router.get("/google")
async def google_login():
    return await AuthController.google_login()

@auth_router.get("/google/callback")
async def google_callback():
    return await AuthController.google_callback()

# Protected routes
@auth_router.post("/logout")
async def logout():
    return await require_auth(AuthController.logout)()

@auth_router.get("/me")
async def get_current_user():
    return await require_auth(AuthController.get_current_user)()

