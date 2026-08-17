from fastapi import Header, HTTPException
from app.database import get_user_by_api_key


def require_user(x_api_key: str = Header(..., description="Your personal API key from /auth/register")):
    """Every protected endpoint depends on this. Each developer/user passes
    their OWN key in the X-API-Key header — this is how the service tells
    users apart and finds their resume/template/contacts, without any
    credentials being hardcoded anywhere in the app."""
    user = get_user_by_api_key(x_api_key)
    if not user:
        raise HTTPException(401, "Invalid or missing API key.")
    return user
