# routers/upload.py
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from utils.storage import storage as storage_engine
from dependencies import get_current_provider

router = APIRouter(prefix="/files", tags=["File Management"])

def format_url(raw_url: str) -> str:
    if raw_url.startswith("http"): return raw_url
    return f"/{raw_url}" if not raw_url.startswith("/") else raw_url


@router.post("/provider/profile-photo")
async def upload_provider_photo(file: UploadFile = File(...), db: Session = Depends(get_db), current_provider: models.ServiceProvider = Depends(get_current_provider)):
    if not file.content_type.startswith("image/"): raise HTTPException(status_code=400, detail="Only images are allowed.")
    
    raw_url = storage_engine.upload_file(await file.read(), file.filename.split(".")[-1], folder_name="uploads/profiles")
    final_url = format_url(raw_url)

    if current_provider.profile_photo_url:
        storage_engine.delete_file(current_provider.profile_photo_url.lstrip("/"))

    current_provider.profile_photo_url = final_url
    db.commit()
    return {"message": "Profile photo updated", "url": final_url}


@router.delete("/provider/profile-photo")
async def remove_provider_photo(db: Session = Depends(get_db), current_provider: models.ServiceProvider = Depends(get_current_provider)):
    if not current_provider.profile_photo_url: raise HTTPException(status_code=400, detail="No profile photo to delete.")
    
    if storage_engine.delete_file(current_provider.profile_photo_url.lstrip("/")):
        current_provider.profile_photo_url = None
        db.commit()
        return {"message": "Profile photo removed successfully."}
    raise HTTPException(status_code=500, detail="Failed to delete file.")


@router.post("/medical-report/{booking_id}")
async def upload_medical_report(
    booking_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_provider: models.ServiceProvider = Depends(get_current_provider)
):
    booking = db.query(models.Booking).filter(models.Booking.booking_id == booking_id).first()
    if not booking: raise HTTPException(status_code=404, detail="Booking not found.")
    if str(booking.provider_id) != str(current_provider.provider_id): raise HTTPException(status_code=403, detail="Not authorized.")

    raw_url = storage_engine.upload_file(await file.read(), file.filename.split(".")[-1], folder_name="uploads/medical_records")
    final_url = format_url(raw_url)

    # 🚨 FIX: Actually attach the report to the booking so the Patient Dashboard can see it!
    # Ensure your models.Booking has `report_url = Column(String(500), nullable=True)`
    booking.report_url = final_url
    booking.booking_status = "completed"
    booking.clinical_notes = "Medical Report & Prescription Attached."
    
    db.commit()

    return {"message": "Medical report uploaded securely.", "url": final_url}

@router.post("/booking/report")
async def upload_booking_report(file: UploadFile = File(...)):
    if not file.content_type.startswith(("image/", "application/pdf")):
        raise HTTPException(status_code=400, detail="Only images and PDFs are allowed.")

    filename_parts = file.filename.split(".")
    raw_url = storage_engine.upload_file(await file.read(), filename_parts[-1] if len(filename_parts) > 1 else "pdf", folder_name="uploads/reports")
    final_url = format_url(raw_url)

    return {"status": "Success", "message": "Report uploaded successfully", "url": final_url, "file_url": final_url }