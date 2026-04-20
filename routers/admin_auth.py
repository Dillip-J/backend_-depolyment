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
    
    # 🚨 DEBUGGING: Print exactly what the frontend is sending
    print(f"\n--- 🕵️ LOGIN ATTEMPT ---")
    print(f"Attempted Email: '{creds.email}'")
    print(f"Attempted Password: '{creds.password}'")

    # 1. Look in Admins table (Case-insensitive search)
    admin = db.query(models.Admin).filter(
        models.Admin.email.ilike(creds.email) # ilike ignores upper/lowercase
    ).first()
    
    if not admin:
        print("❌ FAILED: Email not found in database!")
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    # 2. Verify Hash
    if not verify_password(creds.password, admin.password):
        print("❌ FAILED: Password does not match the database hash!")
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    print("✅ SUCCESS: Credentials match!")

    # Safely get the ID
    primary_id = getattr(admin, "admin_id", getattr(admin, "id", None))

    # 3. Create VIP Token 
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