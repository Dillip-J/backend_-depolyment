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
SECRET_KEY = "your_super_secret_key" 
ALGORITHM = "HS256"

router = APIRouter(prefix="/auth", tags=["Patient Authentication"])

# --- 1. PATIENT SIGNUP (REGISTRATION) ROUTE ---
# Your frontend is trying to hit /users/register, so we will map it here.
# Note: If you want to keep prefixes clean, you might want to change your 
# frontend fetch to hit /auth/register, but we will make this match your current JS.
@router.post("/register", response_model=schemas.UserOut)
def register_patient(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Check if email already exists
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Hash the password
    hashed_password = get_password_hash(user.password)

    # 3. Create the new user object
    # Assuming your User model uses 'user_id' as the primary key UUID
    new_user = models.User(
        user_id=str(uuid.uuid4()), 
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
# CRITICAL FIX: Changed from schemas.UserLogin to OAuth2PasswordRequestForm
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. Look up the user. 
    # Notice we use form_data.username here because FastAPI demands that specific variable name, 
    # even though we are actually passing the user's email address from the frontend.
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
# This tells FastAPI where to look for the token
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
# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from database import get_db
# from models.user import User  # Points directly to the file above
# from schemas import UserCreate, UserLogin

# router = APIRouter(prefix="/auth", tags=["Authentication"])

# @router.post("/register")
# def register(user_data: UserCreate, db: Session = Depends(get_db)):
#     # Check if user exists
#     if db.query(User).filter(User.email == user_data.email).first():
#         raise HTTPException(status_code=400, detail="Email already registered")
    
#     new_user = User(**user_data.dict())
#     db.add(new_user)
#     db.commit()
#     return {"message": "Registered successfully"}

# @router.post("/login")
# def login(creds: UserLogin, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.email == creds.email, User.password == creds.password).first()
#     if not user:
#         raise HTTPException(status_code=401, detail="Invalid credentials")
#     return {"message": "Login successful", "user_id": user.user_id}