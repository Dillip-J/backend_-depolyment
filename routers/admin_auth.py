# routers/admin_auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

# IMPORT SECURITY TOOLS
from utils.security import verify_password, create_access_token

router = APIRouter(prefix="/admin-auth", tags=["Admin Authentication"])

# --- 1. EXCLUSIVE ADMIN LOGIN ROUTE ---
@router.post("/login")
def admin_login(creds: schemas.UserLogin, db: Session = Depends(get_db)):
    # 1. Look in Admins table
    admin = db.query(models.Admin).filter(models.Admin.email == creds.email).first()
    
    # 2. Verify Hash
    if not admin or not verify_password(creds.password, admin.password):
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    # Safely get the ID (Handles whether you named the column 'id' or 'admin_id')
    primary_id = getattr(admin, "admin_id", getattr(admin, "id", None))

    # 3. Create VIP Token (Role is 'admin' for the bouncer to pass)
    access_token = create_access_token(data={"sub": str(primary_id), "role": "admin"})

    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "admin": {
            "admin_id": str(primary_id),
            "name": admin.name,
            "email": admin.email,
            "role": admin.role
        }
    }