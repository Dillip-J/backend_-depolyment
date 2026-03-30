# routers/booking.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from database import get_db
import models, schemas
from uuid import UUID

# IMPORT THE BOUNCER
from dependencies import get_current_user

router = APIRouter(prefix="/bookings", tags=["Bookings"])

# ==========================================
# 1. CREATE (To Book)
# ==========================================
@router.post("/")
def create_booking(
    data: schemas.BookingCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # <-- THE LOCK
):
    # We manually inject the secure user_id from the token into the database model
    booking = models.Booking(
        user_id=current_user.user_id, 
        **data.model_dump(), 
        booking_status="pending"
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return {"id": booking.booking_id, "status": "Success"}

# ==========================================
# 2. CANCEL (To Cancel)
# ==========================================
@router.patch("/{booking_id}/cancel")
def cancel_booking(
    booking_id: UUID, # Ensure it expects a UUID, not an int
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # <-- THE LOCK
):
    # Mathematically guarantees they can only cancel THEIR OWN bookings
    booking = db.query(models.Booking).filter(
        models.Booking.booking_id == booking_id, 
        models.Booking.user_id == current_user.user_id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found or unauthorized")
    
    if booking.booking_status == "canceled":
        raise HTTPException(status_code=400, detail="Booking is already canceled")
        
    booking.booking_status = "canceled"
    db.commit()
    return {"message": "Booking Canceled successfully"}

# ==========================================
# 3. HISTORY (Previous Orders)
# ==========================================
@router.get("/me/history") # Changed from /user/{user_id}/history
def get_my_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # <-- THE LOCK
):
    bookings = db.query(models.Booking)\
        .options(joinedload(models.Booking.provider))\
        .filter(
            models.Booking.user_id == current_user.user_id, 
            models.Booking.booking_status.in_(["completed", "canceled", "rejected"])
        )\
        .order_by(models.Booking.created_at.desc())\
        .all()
        
    return bookings

# ==========================================
# 4. ACTIVE (Upcoming Bookings)
# ==========================================
@router.get("/me/active") # Changed from /user/{user_id}/active
def get_my_active_bookings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # <-- THE LOCK
):
    bookings = db.query(models.Booking)\
        .options(joinedload(models.Booking.provider))\
        .filter(
            models.Booking.user_id == current_user.user_id, 
            models.Booking.booking_status.in_(["pending", "confirmed", "in_transit"])
        )\
        .order_by(models.Booking.scheduled_time.asc())\
        .all()
        
    return bookings
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