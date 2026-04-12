# routers/feedback.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from database import get_db
from datetime import date, datetime, time
import models

# 🚨 THE FIX: IMPORT THE BOUNCER
from dependencies import get_current_provider

router = APIRouter(prefix="/provider", tags=["Doctor Dashboard"])

# 🚨 THE FIX: Change to /me so they can't spy on other doctors
@router.get("/dashboard/me")
def get_provider_schedule(
    db: Session = Depends(get_db),
    current_provider: models.ServiceProvider = Depends(get_current_provider) # 🔒 SECURED
):
    # Extract the secure ID from the validated token
    provider_id = current_provider.provider_id

    # 1. Get the start and end of "Today"
    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)

    # 2. Query bookings for this provider, only for today
    appointments = db.query(models.Booking)\
        .options(
            joinedload(models.Booking.user),
            joinedload(models.Booking.doctor_service) # 🚨 THE FIX: Load this to prevent crashes!
        )\
        .filter(
            models.Booking.provider_id == provider_id,
            models.Booking.scheduled_time >= today_start,
            models.Booking.scheduled_time <= today_end,
            models.Booking.booking_status != "canceled"
        )\
        .order_by(models.Booking.scheduled_time.asc())\
        .all()

    # 3. Format the response for the Doctor's UI
    return {
        "date": date.today(),
        "total_appointments": len(appointments),
        "schedule": [
            {
                "booking_id": app.booking_id,
                "patient_name": app.user.name if app.user else "Unknown Patient", 
                "time": app.scheduled_time.strftime("%H:%M") if app.scheduled_time else "ASAP",
                "status": app.booking_status,
                "service": app.doctor_service.service_name if app.doctor_service else "General Booking"
            }
            for app in appointments
        ]
    }
# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from sqlalchemy.exc import IntegrityError
# from database import get_db
# from models import Review, Complaint
# from schemas import ReviewCreate, ComplaintCreate

# router = APIRouter(prefix="/feedback", tags=["Reviews & Complaints"])

# @router.post("/review", status_code=status.HTTP_201_CREATED)
# def post_review(review_data: ReviewCreate, db: Session = Depends(get_db)):
#     try:
#         new_review = Review(
#             booking_id=review_data.booking_id,
#             rating=review_data.rating,
#             comment=review_data.comment
#         )
#         db.add(new_review)
#         db.commit()
#         db.refresh(new_review)
#         return {"message": "Review submitted", "review_id": new_review.review_id}
    
#     except IntegrityError:
#         db.rollback()
#         # This triggers if a review for the booking_id already exists (Unique constraint)
#         raise HTTPException(status_code=400, detail="Review already exists for this booking")

# @router.post("/complaint", status_code=status.HTTP_201_CREATED)
# def file_complaint(complaint_data: ComplaintCreate, db: Session = Depends(get_db)):
#     new_complaint = Complaint(
#         booking_id=complaint_data.booking_id,
#         user_id=complaint_data.user_id,
#         provider_id=complaint_data.provider_id,
#         complaint_text=complaint_data.complaint_text
#     )
#     db.add(new_complaint)
#     db.commit()
#     db.refresh(new_complaint)
#     return {"message": "Complaint filed successfully", "complaint_id": new_complaint.complaint_id}