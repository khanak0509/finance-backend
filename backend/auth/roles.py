from fastapi import Depends, HTTPException
from backend.auth.auth import get_current_user

def require_role(*allowed_roles: str):
    def role_dependency(user: dict = Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return Depends(role_dependency)
