from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from app.auth import verify_password, create_access_token, get_current_user, UserSession
from app.db import get_db

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    name: str

@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = get_db()
    user = db["users"].find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["passwordHash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"], "name": user["name"]}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user["role"],
        "name": user["name"]
    }

# Backup JSON login endpoint for easier frontend API calls without form data
@router.post("/login/json", response_model=TokenResponse)
def login_json(request: LoginRequest):
    db = get_db()
    user = db["users"].find_one({"email": request.email})
    if not user or not verify_password(request.password, user["passwordHash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"], "name": user["name"]}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user["role"],
        "name": user["name"]
    }

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(current_user: UserSession = Depends(get_current_user)):
    access_token = create_access_token(
        data={"sub": current_user.email, "role": current_user.role, "name": current_user.name}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": current_user.role,
        "name": current_user.name
    }

@router.get("/profile", response_model=UserSession)
def get_profile(current_user: UserSession = Depends(get_current_user)):
    return current_user
