# routers/admin_auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

# IMPORT SECURITY TOOLS
from utils.security import verify_password, create_access_token, hash_password

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

# --- 2. THE BOOTSTRAP DOOR (Temporary) ---
@router.post("/bootstrap-first-admin", summary="⚠️ DEV ONLY: Create First Admin")
def create_first_admin(admin_data: schemas.UserCreate, db: Session = Depends(get_db)):
    admin_count = db.query(models.Admin).count()
    if admin_count > 0:
        raise HTTPException(status_code=403, detail="BOOTSTRAP LOCKED: Admin already exists.")
    
    new_admin = models.Admin(
        name=admin_data.name,
        email=admin_data.email,
        password=hash_password(admin_data.password),
        role="admin" 
    )
    db.add(new_admin)
    db.commit()
    return {"message": "✅ Success! Master Admin created. DELETE THIS ROUTE NOW."}