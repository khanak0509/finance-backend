from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from backend.db.database import get_db
from backend.helpers.jwt import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["is_active"] != 1:
        raise HTTPException(status_code=403, detail="Inactive user")
        
    return dict(user)