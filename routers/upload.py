# routers/upload.py
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from utils.storage import storage as storage_engine

# IMPORT THE BOUNCERS
from dependencies import get_current_provider, get_current_user

router = APIRouter(prefix="/files", tags=["File Management"])

# ==========================================
# PROFILE PHOTOS (Create, Update, Delete)
# ==========================================

@router.post("/provider/profile-photo")
async def upload_provider_photo(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_provider: models.ServiceProvider = Depends(get_current_provider) # <-- THE LOCK
):
    # Security: Verify it's actually an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only images are allowed for profiles.")

    # We NO LONGER need to query the DB or use a hardcoded ID. 
    # The Bouncer guarantees `current_provider` is real and logged in.

    file_bytes = await file.read()
    file_extension = file.filename.split(".")[-1]
    
    new_url = storage_engine.upload_file(file_bytes, file_extension, folder_name="profiles")
    
    # If they already had a photo, delete the old one to save space
    if current_provider.profile_photo_url:
        storage_engine.delete_file(current_provider.profile_photo_url)
        
    # Save the new URL directly to the provider object the Bouncer handed us
    current_provider.profile_photo_url = new_url
    db.commit()
    
    return {"message": "Profile photo updated successfully", "url": new_url}


@router.delete("/provider/profile-photo")
async def remove_provider_photo(
    db: Session = Depends(get_db),
    current_provider: models.ServiceProvider = Depends(get_current_provider) # <-- THE LOCK
):
    if not current_provider.profile_photo_url:
        raise HTTPException(status_code=400, detail="No profile photo to delete.")

    # Delete the actual file from storage
    success = storage_engine.delete_file(current_provider.profile_photo_url)
    
    if success:
        # Remove the link from the database
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
    # 🚨 THE FIX: Only Providers can upload reports now, not Patients!
    current_provider: models.ServiceProvider = Depends(get_current_provider) 
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
    
    new_record = models.MedicalRecord(
        booking_id=booking.booking_id,
        user_id=booking.user_id,
        provider_id=booking.provider_id,
        diagnosis="Report Uploaded via Provider API", 
        report_url=file_url
    )
    db.add(new_record)
    
    # 🚨 Auto-complete the booking once the report is attached
    booking.booking_status = "completed"
    
    db.commit()
    
    return {"message": "Medical report uploaded securely and linked to patient.", "url": file_url}