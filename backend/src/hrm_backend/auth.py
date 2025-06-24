from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, Request, Response
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import os
import secrets

from .database import get_db
from .models import User, UserRole

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
SESSION_EXPIRE_HOURS = 24

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Session serializer
session_serializer = URLSafeTimedSerializer(SECRET_KEY)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

def create_session_token(user_id: int) -> str:
    """Create signed session token"""
    return session_serializer.dumps({"user_id": user_id, "created_at": datetime.utcnow().isoformat()})

def verify_session_token(token: str) -> Optional[dict]:
    """Verify and decode session token"""
    try:
        # Verify signature and expiry (24 hours)
        data = session_serializer.loads(token, max_age=SESSION_EXPIRE_HOURS * 3600)
        return data
    except (BadSignature, SignatureExpired):
        return None

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username, User.is_active == True).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.user_id == user_id, User.is_active == True).first()

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Get current authenticated user from session"""
    # Check for session token in cookies
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Verify session token
    session_data = verify_session_token(session_token)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    # Get user from database
    user = get_user_by_id(db, session_data["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Role-based access control decorators
def require_role(required_role: UserRole):
    """Decorator to require specific user role"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role.value}"
            )
        return current_user
    return role_checker

def require_hr_admin():
    """Require HR Admin role"""
    return require_role(UserRole.HR_ADMIN)

def require_supervisor_or_admin():
    """Require Supervisor or HR Admin role"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in [UserRole.SUPERVISOR, UserRole.HR_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Required role: Supervisor or HR Admin"
            )
        return current_user
    return role_checker

def require_employee_or_admin():
    """Require Employee or HR Admin role (for personal data access)"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in [UserRole.EMPLOYEE, UserRole.HR_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Required role: Employee or HR Admin"
            )
        return current_user
    return role_checker