# utils/security.py
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

# 1. The Master Keys (MUST match dependencies.py)
SECRET_KEY = "VISION_HEALTH_ULTRA_SECRET" # In production, hide this in a .env file!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 Day token

# 2. The Bcrypt Engine
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# 3. The Token Minting Press
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # This creates the mathematically signed gibberish string
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Add this function to securely hash passwords for new users
def get_password_hash(password: str):
    return pwd_context.hash(password)