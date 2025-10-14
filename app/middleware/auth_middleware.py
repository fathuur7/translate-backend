from flask import session, jsonify
from functools import wraps

def require_auth(f):
    """Middleware to check if user is authenticated"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get("user")
        
        if not user:
            return jsonify({
                "error": "Authentication required",
                "message": "Please login to access this resource"
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_verified_email(f):
    """Middleware to check if user's email is verified"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get("user")
        
        if not user:
            return jsonify({
                "error": "Authentication required"
            }), 401
        
        if not user.get("email_verified"):
            return jsonify({
                "error": "Email verification required",
                "message": "Please verify your email to access this resource"
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def optional_auth(f):
    """Middleware that allows both authenticated and unauthenticated access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Just pass through, the route can check session if needed
        return f(*args, **kwargs)
    
    return decorated_function
