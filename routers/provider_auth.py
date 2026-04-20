# routers/provider_auth.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from utils.storage import storage as storage_engine
from utils.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/providers", tags=["Provider Authentication"])

# ==========================================
# --- 1. Registration ---
# ==========================================
@router.post("/register")
async def register_provider(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    provider_type: str = Form(...),
    category: str = Form(...),
    latitude: float = Form(None), 
    longitude: float = Form(None),
    license_document: UploadFile = File(None), 
    db: Session = Depends(get_db)
):
    if db.query(models.ServiceProvider).filter(models.ServiceProvider.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    file_url = None
    if license_document:
        file_bytes = await license_document.read()
        file_extension = license_document.filename.split(".")[-1]
        file_url = storage_engine.upload_file(file_bytes, file_extension, folder_name="provider_licenses")

    hashed_pw = hash_password(password)

    new_provider = models.ServiceProvider(
        name=name,
        email=email,
        phone=phone,
        password=hashed_pw, 
        provider_type=provider_type,
        category=category,
        latitude=latitude, 
        longitude=longitude,
        license_document_url=file_url, 
        status="approved" # Automatically approved for immediate access
    )
    
    db.add(new_provider)
    db.commit()
    return {"message": "Application submitted and approved. You can now log in."}

# ==========================================
# --- 2. Login ---
# ==========================================
@router.post("/login")
def login_provider(creds: schemas.ProviderLogin, db: Session = Depends(get_db)):
    provider = db.query(models.ServiceProvider).filter(models.ServiceProvider.email == creds.email).first()
    
    if not provider or not verify_password(creds.password, provider.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    token = create_access_token(data={"sub": str(provider.provider_id), "role": "provider"})
        
    return {
        "access_token": token,
        "token_type": "bearer",
        "provider": {
            "provider_id": provider.provider_id, 
            "type": provider.provider_type, 
            "name": provider.name,
            "category": getattr(provider, "category", "General"),
            "profile_photo_url": getattr(provider, "profile_photo_url", None)
        }
    }