# dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from database import get_db
import models

# 1. These MUST match the keys in your login routes!
SECRET_KEY = "VISION_HEALTH_ULTRA_SECRET" 
ALGORITHM = "HS256"

# 2. This tells FastAPI to look for the "Authorization: Bearer <token>" header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def verify_token(token: str, credentials_exception):
    """Decodes the JWT and extracts the user ID."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return user_id
    except JWTError:
        raise credentials_exception

# ==========================================
# THE 3 BOUNCERS (GUARDS)
# ==========================================

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Guard for Patient Routes"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = verify_token(token, credentials_exception)
    
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_provider(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Guard for Doctor/Pharmacy/Lab Routes"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid provider credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    provider_id = verify_token(token, credentials_exception)
    
    provider = db.query(models.ServiceProvider).filter(models.ServiceProvider.provider_id == provider_id).first()
    if provider is None:
        raise credentials_exception
    return provider


def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Guard for Admin Dashboard Routes"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    admin_id = verify_token(token, credentials_exception)
    
    admin = db.query(models.Admin).filter(models.Admin.admin_id == admin_id).first()
    if admin is None:
        raise credentials_exception
    return admin