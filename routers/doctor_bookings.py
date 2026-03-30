# routers/doctor_bookings.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from database import get_db
from datetime import date, datetime, time
import models

router = APIRouter(prefix="/provider", tags=["Doctor Dashboard"])

@router.get("/dashboard/{provider_id}")
def get_provider_schedule(provider_id: int, db: Session = Depends(get_db)):
    # 1. Get the start and end of "Today"
    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)

    # 2. Query bookings for this provider, only for today
    # We use joinedload to get the Patient (User) details in the same call
    appointments = db.query(models.Booking)\
        .options(joinedload(models.Booking.user))\
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
                "patient_name": app.user.name,  # Relationship access
                "time": app.scheduled_time.strftime("%H:%M"),
                "status": app.booking_status,
                "service": app.service.service_name
            }
            for app in appointments
        ]
    }