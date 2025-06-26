from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session

from .. import schemas
from ..auth import (
    authenticate_user, 
    create_session_token, 
    get_password_hash,
    get_current_active_user
)
from ..database import get_db
from .. import models
from ..models import User

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=schemas.UserResponse)
def register_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user (admin only in production)"""
    # Check if username already exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    # Check if email already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/login")
def login_user(
    user_credentials: schemas.UserLogin,
    response: Response,
    db: Session = Depends(get_db)
):
    """Login user and set session cookie"""
    user = authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create session token
    session_token = create_session_token(user.user_id)
    
    # Set secure session cookie (expires when browser closes)
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax"
        # No max_age = session cookie (expires when browser closes)
    )
    
    return {"message": "Login successful", "user": {
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role.value
    }}

@router.get("/me", response_model=schemas.UserResponse)
def read_current_user(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Get current user information with associated employee if exists"""
    # Fetch the associated employee for this user
    employee = db.query(models.Employee).filter(models.Employee.user_id == current_user.user_id).first()
    
    # Create response with employee info if available
    user_data = {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
        "employee": employee
    }
    
    return user_data

@router.post("/logout")
def logout_user(response: Response):
    """Logout user by clearing session cookie"""
    response.delete_cookie(
        key="session_token",
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax"
    )
    return {"message": "Successfully logged out"}