# # routers/records.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from database import get_db
import models

router = APIRouter(prefix="/records", tags=["Medical Records"])

@router.get("/user/{user_id}")
def get_medical_history(user_id: int, db: Session = Depends(get_db)):
    # Fetch records and pre-load the linked booking and service data
    records = db.query(models.MedicalRecord)\
        .options(
            joinedload(models.MedicalRecord.booking)
            .joinedload(models.Booking.service)
        )\
        .filter(models.MedicalRecord.user_id == user_id)\
        .order_by(models.MedicalRecord.created_at.desc())\
        .all()
    
    # We return the ORM objects; FastAPI uses the schemas to format the JSON
    return records
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