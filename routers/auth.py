# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

# IMPORT FROM OUR CENTRAL SECURITY ENGINE
from utils.security import verify_password, get_password_hash, create_access_token
import uuid

# 🚨 IMPORTANT: These MUST match exactly what is inside your utils/security.py file!
from utils.security import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/auth", tags=["Patient Authentication"])

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
    # 🚨 FIX APPLIED: Let the database auto-generate the user_id securely!
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


# --- 2. PATIENT LOGIN ROUTE ---
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. Look up the user. 
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    
    # 2. Verify Password Hash
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # 3. Create the Patient Token
    access_token = create_access_token(data={"sub": str(user.user_id), "role": "user"})

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


# --- 3. THE BOUNCER (Token Decoder) ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 1. Decode the Token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 2. Extract the user_id
        user_id_str: str = payload.get("sub") 
        if user_id_str is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception       
    
    # 3. Fetch the User from the Database
    user = db.query(models.User).filter(models.User.user_id == user_id_str).first()
    if user is None:
        raise credentials_exception      
    
    # 4. Pass the full User object to the route!
    return user
