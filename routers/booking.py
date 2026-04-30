# routers/booking.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from database import get_db
import models, schemas
from dependencies import get_current_user
from datetime import datetime, timedelta

router = APIRouter(prefix="/bookings", tags=["Bookings"])

def get_uid(user_obj):
    if isinstance(user_obj, dict):
        return user_obj.get("user_id", user_obj.get("id", user_obj.get("sub")))
    return getattr(user_obj, "user_id", getattr(user_obj, "id", None))

# ==========================================================
# 🧹 THE AUTO-CANCEL JANITOR (Compatible with OLD models)
# ==========================================================
def auto_clean_expired_bookings(db: Session):
    # Sweeps for bookings 24 hours past their scheduled time that were never completed
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    
    expired_bookings = db.query(models.Booking).filter(
        models.Booking.booking_status.in_(["pending", "confirmed", "in_transit"]),
        models.Booking.scheduled_time < cutoff_time
    ).all()
    
    for b in expired_bookings:
        b.booking_status = "canceled"
        # We don't touch clinical_notes here because your old DB doesn't have it!
    
    if expired_bookings:
        db.commit()


@router.post("/")
def create_booking(data: schemas.BookingCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    uid = get_uid(current_user)
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid user session")
    
    patient_age = getattr(data, "patient_age", getattr(data, "age", 0))
    if patient_age <= 0 or patient_age >= 120:
        raise HTTPException(status_code=400, detail="Invalid age provided. Must be between 1 and 119.")

    # 🚨 THE DOUBLE BOOKING FIREWALL
    if data.scheduled_time:
        existing_booking = db.query(models.Booking).filter(
            models.Booking.provider_id == data.provider_id,
            models.Booking.scheduled_time == data.scheduled_time,
            models.Booking.booking_status.in_(["pending", "confirmed", "in_transit"]) 
        ).first()

        if existing_booking:
            if str(existing_booking.user_id) == str(uid):
                raise HTTPException(status_code=400, detail="You have already booked this exact time slot. Please check your dashboard.")
            raise HTTPException(status_code=400, detail="Sorry, this time slot was just booked by someone else.")

    try:
        booking_data = data.model_dump(exclude_unset=True) 
    except AttributeError:
        booking_data = data.dict(exclude_unset=True) 

    booking_data["user_id"] = uid
    booking_data["booking_status"] = "confirmed" 

    booking = models.Booking(**booking_data)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    
    return {"booking_id": booking.booking_id, "id": booking.booking_id, "status": "Success"}


@router.patch("/{booking_id}/cancel")
def cancel_booking(booking_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    uid = get_uid(current_user)
    booking = db.query(models.Booking).filter(models.Booking.booking_id == booking_id, models.Booking.user_id == uid).first()
    if not booking: raise HTTPException(status_code=404, detail="Booking not found")
    booking.booking_status = "canceled"
    db.commit()
    return {"message": "Booking Canceled successfully"}


@router.get("/me/history")
def get_my_history(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    uid = get_uid(current_user)
    auto_clean_expired_bookings(db) # 🧹 Run Janitor
    
    return db.query(models.Booking).options(joinedload(models.Booking.provider))\
        .filter(models.Booking.user_id == uid, models.Booking.booking_status.in_(["completed", "canceled", "rejected"]))\
        .order_by(models.Booking.created_at.desc()).all()


@router.get("/me/active")
def get_my_active_bookings(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    uid = get_uid(current_user)
    auto_clean_expired_bookings(db) # 🧹 Run Janitor
    
    return db.query(models.Booking).options(joinedload(models.Booking.provider))\
        .filter(models.Booking.user_id == uid, models.Booking.booking_status.in_(["pending", "confirmed", "in_transit"]))\
        .order_by(models.Booking.created_at.desc()).all()


@router.get("/{booking_id}")
def get_single_booking(booking_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    uid = get_uid(current_user)
    booking = db.query(models.Booking).options(joinedload(models.Booking.provider)).filter(
        models.Booking.booking_id == booking_id, models.Booking.user_id == uid
    ).first()
    
    if not booking: raise HTTPException(status_code=404, detail="Booking not found")
        
    v_type = "Home Visit"
    addr = (booking.delivery_address or "").strip().lower()
    if booking.provider and getattr(booking.provider, "provider_type", None) == "Pharmacy":
        v_type = "Delivery"
    elif addr in ["none", "null", "", "platform default", "online", "undefined"]:
        v_type = "Video Consult"

    return {
        "display_id": booking.booking_id,
        "raw_id": booking.booking_id,
        "doctor_name": booking.provider.name if booking.provider else "Unknown",
        "specialty": booking.provider.category if booking.provider else "Specialist",
        "date": booking.scheduled_time.strftime("%A, %B %d, %Y") if booking.scheduled_time else "ASAP",
        "time": booking.scheduled_time.strftime("%I:%M %p") if booking.scheduled_time else "TBD",
        "visit_type": v_type,
        "address": booking.delivery_address if v_type != "Video Consult" else "Secure Google Meet Invite",
        "patient_name": getattr(booking, "patient_name", "Self"),
        "status": booking.booking_status.lower() 
    }
# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session, joinedload
# from database import get_db
# import models, schemas

# router = APIRouter(prefix="/bookings", tags=["Bookings"])

# @router.post("/")
# def create_booking(data: schemas.BookingCreate, db: Session = Depends(get_db)):
#     new_booking = models.Booking(**data.model_dump(), booking_status="pending")
#     db.add(new_booking)
#     db.commit()
#     return {"booking_id": new_booking.booking_id}

# @router.patch("/{booking_id}/cancel")
# def cancel_booking(booking_id: int, user_id: int, db: Session = Depends(get_db)):
#     booking = db.query(models.Booking).filter(models.Booking.booking_id == booking_id, models.Booking.user_id == user_id).first()
#     if not booking: raise HTTPException(status_code=404)
#     booking.booking_status = "canceled"
#     db.commit()
#     return {"message": "Canceled"}
# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session, joinedload
# from database import get_db
# import models, schemas

# router = APIRouter(prefix="/bookings", tags=["Bookings"])

# @router.post("/", status_code=status.HTTP_201_CREATED)
# def create_booking(booking_data: schemas.BookingCreate, db: Session = Depends(get_db)):
#     new_booking = models.Booking(**booking_data.model_dump(), booking_status="pending")
#     db.add(new_booking)
#     db.commit()
#     db.refresh(new_booking)
#     return {"message": "Booking request sent", "booking_id": new_booking.booking_id}

# @router.get("/user/{user_id}")
# def get_user_bookings(user_id: int, db: Session = Depends(get_db)):
#     return db.query(models.Booking)\
#         .options(joinedload(models.Booking.service), joinedload(models.Booking.provider))\
#         .filter(models.Booking.user_id == user_id)\
#         .order_by(models.Booking.scheduled_time.desc()).all()
# # Add to routers/booking.py

# @router.patch("/{booking_id}/cancel")
# def cancel_appointment(booking_id: int, user_id: int, db: Session = Depends(get_db)):
#     # 1. Find the booking and verify it belongs to this user
#     booking = db.query(models.Booking).filter(
#         models.Booking.booking_id == booking_id,
#         models.Booking.user_id == user_id
#     ).first()

#     if not booking:
#         raise HTTPException(status_code=404, detail="Booking not found or access denied")

#     # 2. Check if it's already completed or canceled
#     if booking.booking_status != "pending" and booking.booking_status != "confirmed":
#         raise HTTPException(status_code=400, detail=f"Cannot cancel a booking that is {booking.booking_status}")

#     # 3. Change status
#     booking.booking_status = "canceled"
#     db.commit()

#     return {"message": "Appointment canceled successfully"}
# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session, joinedload
# from database import get_db
# from schemas import BookingCreate
# import models  # Import all models from one place to avoid circular loops

# router = APIRouter(prefix="/bookings", tags=["Bookings"])

# @router.post("/", status_code=status.HTTP_201_CREATED)
# def create_booking(booking_data: BookingCreate, db: Session = Depends(get_db)):
#     # 1. Validation: Use the centralized models file
#     user_exists = db.query(models.User).filter(models.User.user_id == booking_data.user_id).first()
#     if not user_exists:
#         raise HTTPException(status_code=404, detail="User not found")

#     # 2. Create the instance
#     new_booking = models.Booking(
#         user_id=booking_data.user_id,
#         provider_id=booking_data.provider_id,
#         service_id=booking_data.service_id,
#         scheduled_time=booking_data.scheduled_time,
#         booking_status="pending"
#     )
    
#     db.add(new_booking)
#     db.commit()
#     db.refresh(new_booking)
    
#     return {"message": "Booking request sent", "booking_id": new_booking.booking_id}

# @router.get("/user/{user_id}")
# def get_user_bookings(user_id: int, db: Session = Depends(get_db)):
#     # 3. Optimization: Use joinedload to get service and provider in 1 query
#     bookings = db.query(models.Booking)\
#         .options(joinedload(models.Booking.service), joinedload(models.Booking.provider))\
#         .filter(models.Booking.user_id == user_id)\
#         .order_by(models.Booking.scheduled_time.desc())\
#         .all()
    
#     return [
#         {
#             "booking_id": b.booking_id,
#             "service_name": b.service.service_name, 
#             "provider_name": b.provider.name,       
#             "scheduled_time": b.scheduled_time,
#             "booking_status": b.booking_status
#         }
#         for b in bookings
#     ]