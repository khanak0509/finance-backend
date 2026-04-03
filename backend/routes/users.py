from fastapi import APIRouter, Depends, HTTPException, status
from backend.db.database import get_db
from backend.schemas.user import UserResponse, UserStatusUpdate, UserRoleUpdate
from backend.auth.roles import require_role

router = APIRouter(
    prefix="/api/users", 
    tags=["users"],
    dependencies=[require_role("admin")]
)

def _get_user(db, user_id: int):
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(user)

@router.get("", response_model=list[UserResponse])
def get_users(db=Depends(get_db)):
    users_data = db.execute("SELECT * FROM users").fetchall()
    
    # print("users:", len(users_data))
    
    user_list = []
    for u in users_data:
        user_list.append(dict(u))
        
    return user_list

@router.patch("/{id}/status", response_model=UserResponse)
def update_user_status(id: int, payload: UserStatusUpdate, db=Depends(get_db)):
    _get_user(db, id)
    db.execute("UPDATE users SET is_active = ? WHERE id = ?", (payload.is_active, id))
    db.commit()
    return _get_user(db, id)

@router.patch("/{id}/role", response_model=UserResponse)
def update_user_role(id: int, payload: UserRoleUpdate, db=Depends(get_db)):
    _get_user(db, id)
    db.execute("UPDATE users SET role = ? WHERE id = ?", (payload.role, id))
    db.commit()
    return _get_user(db, id)
