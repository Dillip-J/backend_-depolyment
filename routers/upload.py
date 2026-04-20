# routers/upload.py
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from utils.storage import storage as storage_engine
from dependencies import get_current_provider

router = APIRouter(prefix="/files", tags=["File Management"])


def format_url(raw_url: str) -> str:
    """Ensures local files have leading slash, keeps cloud URLs untouched"""
    if raw_url.startswith("http"):
        return raw_url
    return f"/{raw_url}" if not raw_url.startswith("/") else raw_url


@router.post("/provider/profile-photo")
async def upload_provider_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_provider: models.ServiceProvider = Depends(get_current_provider)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only images are allowed.")

    file_bytes = await file.read()
    file_extension = file.filename.split(".")[-1]

    # ✅ FIX: Save inside uploads folder
    raw_url = storage_engine.upload_file(
        file_bytes,
        file_extension,
        folder_name="uploads/profiles"   # 🔥 FIXED
    )

    final_url = format_url(raw_url)

    # delete old image
    if current_provider.profile_photo_url:
        storage_engine.delete_file(current_provider.profile_photo_url.lstrip("/"))

    current_provider.profile_photo_url = final_url
    db.commit()

    return {"message": "Profile photo updated", "url": final_url}


@router.delete("/provider/profile-photo")
async def remove_provider_photo(
    db: Session = Depends(get_db),
    current_provider: models.ServiceProvider = Depends(get_current_provider)
):
    if not current_provider.profile_photo_url:
        raise HTTPException(status_code=400, detail="No profile photo to delete.")

    success = storage_engine.delete_file(
        current_provider.profile_photo_url.lstrip("/")  # ✅ FIX
    )

    if success:
        current_provider.profile_photo_url = None
        db.commit()
        return {"message": "Profile photo removed successfully."}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete file.")


@router.post("/medical-report/{booking_id}")
async def upload_medical_report(
    booking_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_provider: models.ServiceProvider = Depends(get_current_provider)
):
    booking = db.query(models.Booking).filter(
        models.Booking.booking_id == booking_id
    ).first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")

    if str(booking.provider_id) != str(current_provider.provider_id):
        raise HTTPException(status_code=403, detail="Not authorized.")

    file_bytes = await file.read()
    file_extension = file.filename.split(".")[-1]

    # ✅ FIX: Save inside uploads folder
    raw_url = storage_engine.upload_file(
        file_bytes,
        file_extension,
        folder_name="uploads/medical_records"   # 🔥 FIXED
    )

    final_url = format_url(raw_url)

    new_record = models.MedicalRecord(
        booking_id=booking.booking_id,
        diagnosis="Report Uploaded via Provider API",
        report_url=final_url
    )

    db.add(new_record)
    booking.booking_status = "completed"
    db.commit()

    return {"message": "Medical report uploaded securely.", "url": final_url}
