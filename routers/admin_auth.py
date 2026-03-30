# routers/admin_auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

# IMPORT SECURITY TOOLS
from utils.security import verify_password, create_access_token, hash_password

# 🚨 MUST MATCH YOUR PATIENT AUTH SECRET
SECRET_KEY = "your_super_secret_key" 
ALGORITHM = "HS256"

router = APIRouter(prefix="/admin-auth", tags=["Admin Authentication"])

# --- 1. ADMIN LOGIN ROUTE ---
@router.post("/login")
def admin_login(creds: schemas.UserLogin, db: Session = Depends(get_db)):
    # 1. Look in Admins table
    admin = db.query(models.Admin).filter(models.Admin.email == creds.email).first()
    
    # 2. Verify Hash
    if not admin or not verify_password(creds.password, admin.password):
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    # 3. Create VIP Token (Role is 'admin' for the bouncer to pass)
    access_token = create_access_token(data={"sub": str(admin.admin_id), "role": "admin"})

    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "admin": {
            "admin_id": str(admin.admin_id),
            "name": admin.name,
            "email": admin.email,
            "role": admin.role
        }
    }

# --- 2. THE VIP BOUNCER ---
oauth2_admin_scheme = OAuth2PasswordBearer(tokenUrl="admin-auth/login")

def get_current_admin(token: str = Depends(oauth2_admin_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        admin_id_str: str = payload.get("sub")
        role: str = payload.get("role")
        
        # Verify the role is specifically 'admin'
        if admin_id_str is None or role != "admin":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    admin = db.query(models.Admin).filter(models.Admin.admin_id == admin_id_str).first()
    if admin is None:
        raise credentials_exception
    return admin

# --- 3. THE BOOTSTRAP DOOR (Temporary) ---
@router.post("/bootstrap-first-admin", summary="⚠️ DEV ONLY: Create First Admin")
def create_first_admin(admin_data: schemas.UserCreate, db: Session = Depends(get_db)):
    admin_count = db.query(models.Admin).count()
    if admin_count > 0:
        raise HTTPException(status_code=403, detail="BOOTSTRAP LOCKED: Admin already exists.")
    
    new_admin = models.Admin(
        name=admin_data.name,
        email=admin_data.email,
        password=hash_password(admin_data.password),
        role="admin" # Set to 'admin' to match the bouncer's expectation
    )
    db.add(new_admin)
    db.commit()
    return {"message": "✅ Success! Master Admin created. DELETE THIS ROUTE NOW."}