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
# NOTE: get_current_user is defined in dependencies.py and shared across all routers.
# Do not redefine it here to avoid conflicts.

# # routers/auth.py
# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from database import get_db
# import models, schemas

# # IMPORT FROM OUR CENTRAL SECURITY ENGINE
# from utils.security import verify_password, hash_password, create_access_token

# router = APIRouter(prefix="/auth", tags=["Patient Authentication"])

# # --- 1. PATIENT SIGNUP (REGISTRATION) ROUTE ---
# @router.post("/register", response_model=schemas.UserOut)
# def register_patient(user: schemas.UserCreate, db: Session = Depends(get_db)):
#     # 1. Check if email already exists
#     existing_user = db.query(models.User).filter(models.User.email == user.email).first()
#     if existing_user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST, 
#             detail="This email is already registered. Please log in instead."
#         )

#     # 2. Hash the password
#     hashed_password = hash_password(user.password)

#     # 3. Create the new user object
#     new_user = models.User(
#         name=user.name,
#         email=user.email,
#         phone=user.phone,
#         password=hashed_password
#     )

#     # 4. Save to database
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)

#     return new_user


# # --- 2. PATIENT LOGIN ROUTE ---
# @router.post("/login")
# def login(creds: schemas.UserLogin, db: Session = Depends(get_db)):
#     # 1. Look up the user by email
#     user = db.query(models.User).filter(models.User.email == creds.email.lower()).first()
    
#     # 2. Verify Password Hash
#     if not user or not verify_password(creds.password, user.password):
#         raise HTTPException(status_code=401, detail="Invalid email or password")

#     # 3. Create the Patient Token
#     try:
#         access_token = create_access_token(data={"sub": str(user.user_id), "role": "user"})
#     except Exception as e:
#         print(f"JWT GENERATION ERROR: {e}")
#         raise HTTPException(status_code=500, detail="Server Configuration Error: Missing Secret Key")

#     # 4. Return exactly what the Patient frontend needs
#     return {
#         "access_token": access_token, 
#         "token_type": "bearer", 
#         "user": {
#             "user_id": str(user.user_id),
#             "name": user.name,
#             "email": user.email
#         }
#     }


