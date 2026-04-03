from fastapi import APIRouter, Depends, HTTPException, status
from backend.db.database import get_db
from backend.schemas.user import UserCreate, UserLogin, UserResponse, Token
from backend.helpers.hashing import hash_password, verify_password
from backend.helpers.jwt import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db=Depends(get_db)):

    if db.execute("SELECT id FROM users WHERE email = ?", (user.email,)).fetchone():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed = hash_password(user.password)
    cur = db.execute(
        "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
        (user.name, user.email, hashed, user.role)
    )
    db.commit()
    new_user = db.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(new_user)

@router.post("/login", response_model=Token)
def login(user: UserLogin, db=Depends(get_db)):

    db_user = db.execute("SELECT * FROM users WHERE email = ?", (user.email,)).fetchone()
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    if db_user["is_active"] != 1:
        raise HTTPException(status_code=403, detail="Account is disabled")
        
    # generate token for the user
    token = create_access_token({"sub": str(db_user["id"]), "role": db_user["role"]})
    return {"access_token": token, "token_type": "bearer"}