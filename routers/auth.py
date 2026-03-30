# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

# IMPORT FROM OUR CENTRAL SECURITY ENGINE
from utils.security import verify_password, create_access_token

# 🚨 IMPORTANT: These MUST match exactly what is inside your utils/security.py file!
SECRET_KEY = "your_super_secret_key" 
ALGORITHM = "HS256"

router = APIRouter(prefix="/auth", tags=["Patient Authentication"])

# --- 1. PATIENT ONLY LOGIN ROUTE ---
@router.post("/login")
def login(creds: schemas.UserLogin, db: Session = Depends(get_db)):
    # 1. ONLY look in the Users table
    user = db.query(models.User).filter(models.User.email == creds.email).first()
    
    # 2. Verify Password Hash
    if not user or not verify_password(creds.password, user.password):
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

# --- 2. THE BOUNCER (Token Decoder) ---
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