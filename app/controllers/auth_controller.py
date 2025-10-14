from flask import redirect, request, jsonify, session
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
import requests
import os

class AuthController:
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8080")

    @staticmethod
    def google_login():
        """Redirect user to Google OAuth login page"""
        try:
            google_auth_url = (
                "https://accounts.google.com/o/oauth2/v2/auth"
                "?response_type=code"
                f"&client_id={AuthController.GOOGLE_CLIENT_ID}"
                f"&redirect_uri={AuthController.GOOGLE_REDIRECT_URI}"
                "&scope=openid%20email%20profile"
                "&access_type=offline"
                "&prompt=consent"
            )
            return redirect(google_auth_url)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def google_callback():
        """Handle Google OAuth callback"""
        try:
            code = request.args.get("code")
            
            if not code:
                return redirect(f"{AuthController.FRONTEND_URL}/login?error=no_code")

            # Exchange code for access token
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                "code": code,
                "client_id": AuthController.GOOGLE_CLIENT_ID,
                "client_secret": AuthController.GOOGLE_CLIENT_SECRET,
                "redirect_uri": AuthController.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            }
            
            token_response = requests.post(token_url, data=data)
            token_json = token_response.json()

            if "error" in token_json:
                return redirect(f"{AuthController.FRONTEND_URL}/login?error={token_json['error']}")

            # Verify ID token
            idinfo = id_token.verify_oauth2_token(
                token_json["id_token"], 
                grequests.Request(), 
                AuthController.GOOGLE_CLIENT_ID
            )

            # Store user info in session
            user_data = {
                "id": idinfo.get("sub"),
                "email": idinfo["email"],
                "name": idinfo.get("name"),
                "picture": idinfo.get("picture"),
                "email_verified": idinfo.get("email_verified", False)
            }
            
            session["user"] = user_data
            session["access_token"] = token_json["access_token"]
            session["id_token"] = token_json["id_token"]
            
            if "refresh_token" in token_json:
                session["refresh_token"] = token_json["refresh_token"]

            # Redirect to frontend with success
            return redirect(f"{AuthController.FRONTEND_URL}/dashboard?auth=success")

        except ValueError as e:
            # Invalid token
            return redirect(f"{AuthController.FRONTEND_URL}/login?error=invalid_token")
        except Exception as e:
            return redirect(f"{AuthController.FRONTEND_URL}/login?error=server_error")

    @staticmethod
    def logout():
        """Logout user and clear session"""
        try:
            # Revoke Google token if exists
            access_token = session.get("access_token")
            if access_token:
                revoke_url = f"https://oauth2.googleapis.com/revoke?token={access_token}"
                requests.post(revoke_url)
            
            # Clear session
            session.clear()
            
            return jsonify({
                "success": True,
                "message": "Logged out successfully"
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def get_current_user():
        """Get current authenticated user"""
        try:
            user = session.get("user")
            if not user:
                return jsonify({"error": "Not authenticated"}), 401
            
            return jsonify({
                "success": True,
                "user": user
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
