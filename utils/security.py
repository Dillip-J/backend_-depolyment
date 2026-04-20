# utils/security.py
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import os

# 1. The Master Keys
SECRET_KEY = os.getenv("SECRET_KEY", "VISION_HEALTH_ULTRA_SECRET") 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 Day token

# 2. The Bcrypt Engine
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    """Hashes a plaintext password."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    """Verifies a plaintext password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

# 3. The Token Minting Press
def create_access_token(data: dict):
    """Creates a signed JWT."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt