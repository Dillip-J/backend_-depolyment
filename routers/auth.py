# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
import models, schemas

# IMPORT FROM OUR CENTRAL SECURITY ENGINE
from utils.security import verify_password, get_password_hash, create_access_token

router = APIRouter(prefix="/auth", tags=["Patient Authentication"])

# --- NEW: JSON Login Schema ---
class LoginRequest(BaseModel):
    email: str
    password: str

# --- 1. PATIENT SIGNUP (REGISTRATION) ROUTE ---
@router.post("/register", response_model=schemas.UserOut)
def register_patient(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Check if email already exists
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="This email is already registered. Please log in instead."
        )

    # 2. Hash the password
    hashed_password = get_password_hash(user.password)

    # 3. Create the new user object
    new_user = models.User(
        name=user.name,
        email=user.email,
        phone=user.phone,
        password=hashed_password
    )

    # 4. Save to database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# --- 2. PATIENT LOGIN ROUTE (FIXED FOR JSON) ---
@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    # 1. Look up the user by email (Safely handling JSON input)
    user = db.query(models.User).filter(models.User.email == data.email).first()
    
    # 2. Verify Password Hash
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # 3. Create the Patient Token
    try:
        access_token = create_access_token(data={"sub": str(user.user_id), "role": "user"})
    except Exception as e:
        # If this triggers, your SECRET_KEY is missing in Render!
        print(f"JWT GENERATION ERROR: {e}")
        raise HTTPException(status_code=500, detail="Server Configuration Error: Missing Secret Key")

    # 4. Return exactly what the Patient frontend needs
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user": {
            "user_id": str(user.user_id),
            "name": user.name,
            "email": user.email
        }
    }
# NOTE: get_current_user is defined in dependencies.py and shared across all routers.
# Do not redefine it here to avoid conflicts.
