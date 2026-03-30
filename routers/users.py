# routers/users.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from utils.storage import storage as storage_engine
from dependencies import get_current_user # <-- IMPORT THE BOUNCER

router = APIRouter(prefix="/users", tags=["Patient Portal"])

# ==========================================
# 1. PROFILE MANAGEMENT
# ==========================================

@router.get("/me")
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # <-- THE LOCK
):
    """Fetches the securely logged-in user's profile and addresses."""
    addresses = db.query(models.SavedAddress).filter(models.SavedAddress.user_id == current_user.user_id).all()
    
    return {
        "user_id": current_user.user_id,
        "name": current_user.name,
        "email": current_user.email,
        "phone": current_user.phone,
        "profile_photo_url": getattr(current_user, 'profile_photo_url', None), 
        "saved_addresses": addresses
    }

@router.post("/me/profile-photo")
async def update_my_photo(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # <-- THE LOCK
):
    """Uploads a new photo securely and deletes the old one."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only images are allowed.")

    file_bytes = await file.read()
    file_extension = file.filename.split(".")[-1]
    
    # Upload new file
    new_url = storage_engine.upload_file(file_bytes, file_extension, folder_name="user_profiles")
    
    # Delete old file to save storage space
    if getattr(current_user, 'profile_photo_url', None):
        storage_engine.delete_file(current_user.profile_photo_url)
        
    # We can directly modify current_user because the Bouncer fetched it from the DB!
    current_user.profile_photo_url = new_url
    db.commit()
    
    return {"message": "Profile photo updated", "url": new_url}

# ==========================================
# 2. AMAZON-STYLE ADDRESS BOOK
# ==========================================

@router.post("/me/addresses")
def add_my_address(
    address_data: schemas.SavedAddressCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # <-- THE LOCK
):
    """Saves a new 'Home', 'Work', or 'Mom's House' address securely."""
    
    # If this is set as default, remove default from all other addresses owned by this user
    if address_data.is_default:
        db.query(models.SavedAddress).filter(models.SavedAddress.user_id == current_user.user_id).update({"is_default": 0})

    new_address = models.SavedAddress(
        user_id=current_user.user_id, # Cryptographically secure ID
        **address_data.model_dump()
    )
    db.add(new_address)
    db.commit()
    
    return {"message": f"Address '{new_address.label}' saved successfully."}

@router.delete("/me/addresses/{address_id}")
def delete_my_address(
    address_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # <-- THE LOCK
):
    """Deletes a specific saved address."""
    # Notice we query by BOTH address_id AND current_user.user_id
    # This guarantees they can't delete someone else's address!
    address = db.query(models.SavedAddress).filter(
        models.SavedAddress.address_id == address_id,
        models.SavedAddress.user_id == current_user.user_id 
    ).first()
    
    if not address:
        raise HTTPException(status_code=404, detail="Address not found or unauthorized.")
        
    db.delete(address)
    db.commit()
    return {"message": "Address removed successfully."}