# routers/upload.py
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from utils.storage import storage as storage_engine

# IMPORT THE BOUNCER
from dependencies import get_current_provider

router = APIRouter(prefix="/files", tags=["File Management"])

# ==========================================
# PROFILE PHOTOS (Create, Update, Delete)
# ==========================================

@router.post("/provider/profile-photo")
async def upload_provider_photo(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_provider: models.ServiceProvider = Depends(get_current_provider) # 🔒 SECURED
):
    # Security: Verify it's actually an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only images are allowed for profiles.")

    file_bytes = await file.read()
    file_extension = file.filename.split(".")[-1]
    
    new_url = storage_engine.upload_file(file_bytes, file_extension, folder_name="profiles")
    
    # If they already had a photo, delete the old one to save space
    if current_provider.profile_photo_url:
        storage_engine.delete_file(current_provider.profile_photo_url)
        
    current_provider.profile_photo_url = new_url
    db.commit()
    
    return {"message": "Profile photo updated successfully", "url": new_url}


@router.delete("/provider/profile-photo")
async def remove_provider_photo(
    db: Session = Depends(get_db),
    current_provider: models.ServiceProvider = Depends(get_current_provider) # 🔒 SECURED
):
    if not current_provider.profile_photo_url:
        raise HTTPException(status_code=400, detail="No profile photo to delete.")

    # Delete the actual file from storage
    success = storage_engine.delete_file(current_provider.profile_photo_url)
    
    if success:
        current_provider.profile_photo_url = None
        db.commit()
        return {"message": "Profile photo removed successfully."}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete file from storage.")


# ==========================================
# MEDICAL RECORDS (Secure Upload)
# ==========================================

@router.post("/medical-report/{booking_id}")
async def upload_medical_report(
    booking_id: int, 
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_provider: models.ServiceProvider = Depends(get_current_provider) # 🔒 SECURED
):
    # Security check 1: Does this booking exist?
    booking = db.query(models.Booking).filter(models.Booking.booking_id == booking_id).first()
    if not booking:
         raise HTTPException(status_code=404, detail="Booking not found.")
         
    # Security check 2: IDOR Protection. Does this booking belong to THIS Doctor/Lab?
    if str(booking.provider_id) != str(current_provider.provider_id):
        raise HTTPException(status_code=403, detail="Not authorized to upload reports for other providers' bookings.")

    file_bytes = await file.read()
    file_extension = file.filename.split(".")[-1]
    
    file_url = storage_engine.upload_file(file_bytes, file_extension, folder_name="medical_records")
    
    # 🚨 THE FIX: Removed redundant user_id and provider_id to prevent DB crashes
    new_record = models.MedicalRecord(
        booking_id=booking.booking_id,
        diagnosis="Report Uploaded via Provider API", 
        report_url=file_url
    )
    db.add(new_record)
    
    # Auto-complete the booking once the report is attached
    booking.booking_status = "completed"
    
    db.commit()
    
    return {"message": "Medical report uploaded securely and linked to patient.", "url": file_url}