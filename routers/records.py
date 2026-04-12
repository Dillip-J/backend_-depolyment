from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from database import get_db
import models

# 🚨 THE FIX: IMPORT THE BOUNCER
from dependencies import get_current_user

router = APIRouter(prefix="/records", tags=["Medical Records"])

# 🚨 THE FIX: Change to /me so users can ONLY see their own records
@router.get("/me")
def get_my_medical_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # 🔒 SECURED
):
    # 🚨 THE FIX: Join the Booking table to ensure we only get records for THIS specific user
    records = db.query(models.MedicalRecord)\
        .join(models.Booking)\
        .filter(models.Booking.user_id == current_user.user_id)\
        .options(
            joinedload(models.MedicalRecord.booking)
            .joinedload(models.Booking.provider) # Safely load the Doctor/Lab details
        )\
        .order_by(models.MedicalRecord.record_id.desc())\
        .all()
    
    # Format the data cleanly for the frontend
    formatted_records = []
    for r in records:
        formatted_records.append({
            "record_id": r.record_id,
            "booking_id": r.booking_id,
            "diagnosis": r.diagnosis,
            "report_url": getattr(r, 'report_url', None),
            # Extract safe details from the joined Booking/Provider tables
            "provider_name": r.booking.provider.name if r.booking and r.booking.provider else "Unknown Clinic",
            "date": r.booking.scheduled_time.strftime("%d %b, %Y") if r.booking and r.booking.scheduled_time else "Unknown Date"
        })

    return formatted_records
# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session, joinedload
# from database import get_db
# import models

# router = APIRouter(prefix="/records", tags=["Medical Records"])

# @router.get("/user/{user_id}")
# def get_user_medical_history(user_id: int, db: Session = Depends(get_db)):
#     # 1. Fetch records for the specific user
#     # We use joinedload to get 'booking' (which contains the service) 
#     # and 'provider' (the doctor) in one single query.
#     records = db.query(models.MedicalRecord)\
#         .options(
#             joinedload(models.MedicalRecord.booking).joinedload(models.Booking.service),
#             joinedload(models.MedicalRecord.provider)
#         )\
#         .filter(models.MedicalRecord.user_id == user_id)\
#         .order_by(models.MedicalRecord.created_at.desc())\
#         .all()

#     # 2. Format the response for the User UI
#     return [
#         {
#             "record_id": r.record_id,
#             "date": r.created_at,
#             "service_name": r.booking.service.service_name, # Access via nested relationship
#             "doctor_name": r.provider.name,                # Access via relationship
#             "diagnosis": r.diagnosis,
#             "report_url": r.report_url
#         }
#         for r in records
#     ]