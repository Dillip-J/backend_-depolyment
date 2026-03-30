# routers/providers.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, String
from database import get_db
import models, schemas
from datetime import date, datetime, time
from uuid import UUID

# IMPORT OUR SECURITY ENGINE & BOUNCER
from utils.security import hash_password, verify_password, create_access_token
from dependencies import get_current_provider 

router = APIRouter(prefix="/providers", tags=["Service Providers"])

# --- 1. Registration ---
@router.post("/register")
def register_provider(data: schemas.ProviderCreate, db: Session = Depends(get_db)):
    if db.query(models.ServiceProvider).filter(models.ServiceProvider.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # SECURITY FIX: Hash the password before saving!
    hashed_pwd = hash_password(data.password)
    
    # Create dictionary from Pydantic model, swap plain password for hashed one
    provider_data = data.model_dump()
    provider_data["password"] = hashed_pwd
    
    new_provider = models.ServiceProvider(**provider_data, status="pending")
    db.add(new_provider)
    db.commit()
    return {"message": "Application submitted. Awaiting Admin approval."}

# --- 2. Login (Specific to Providers) ---
@router.post("/login")
def login_provider(creds: schemas.ProviderLogin, db: Session = Depends(get_db)):
    provider = db.query(models.ServiceProvider).filter(models.ServiceProvider.email == creds.email).first()
    
    # SECURITY FIX: Verify Hash
    if not provider or not verify_password(creds.password, provider.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    if provider.status == "pending":
        raise HTTPException(status_code=403, detail="Account pending admin approval")
        
    # GENERATE TOKEN
    token = create_access_token(data={"sub": str(provider.provider_id), "role": "provider"})
        
    return {
        "access_token": token,
        "token_type": "bearer",
        "provider": {
            "provider_id": provider.provider_id, 
            "type": provider.provider_type, 
            "name": provider.name,
            "category": provider.category,
            "profile_photo_url": provider.profile_photo_url
        }
    }

# --- 3. Dynamic Dashboard Data (SECURED) ---
@router.get("/dashboard/me") # SECURITY FIX: Removed {provider_id}
def get_provider_dashboard(
    db: Session = Depends(get_db),
    current_provider: models.ServiceProvider = Depends(get_current_provider) # THE LOCK
):
    # No need to check if provider exists; the Bouncer already did!
    provider_id = current_provider.provider_id

    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)
    
    today_count = db.query(models.Booking).filter(
        models.Booking.provider_id == provider_id,
        models.Booking.scheduled_time >= today_start,
        models.Booking.scheduled_time <= today_end
    ).count()

    bookings = db.query(models.Booking)\
        .options(joinedload(models.Booking.user))\
        .filter(models.Booking.provider_id == provider_id)\
        .order_by(models.Booking.created_at.desc())\
        .all()

    formatted_bookings = []
    for b in bookings:
        service_label = "General Request"
        if b.doctor_service_id: service_label = f"Consultation (ID: {b.doctor_service_id})"
        if b.medicine_id: service_label = f"Medicine Order (ID: {b.medicine_id})"
        if b.lab_test_id: service_label = f"Lab Test (ID: {b.lab_test_id})"

        time_str = b.scheduled_time.strftime("%d %b, %H:%M") if b.scheduled_time else b.created_at.strftime("%d %b, ASAP")

        formatted_bookings.append({
            "booking_id": b.booking_id,
            "client_name": b.user.name if b.user else "Unknown Patient",
            "client_phone": b.user.phone if b.user else "N/A",
            "service_name": service_label,
            "time": time_str,
            "status": b.booking_status,
            "address": b.delivery_address if b.delivery_address else "Not Provided",
            "notes": b.order_notes if b.order_notes else "No additional notes",
            "is_delivery": current_provider.provider_type == "Pharmacy"
        })

    return {
        "provider_info": {
            "name": current_provider.name,
            "type": current_provider.provider_type,
            "category": current_provider.category
        },
        "total_today": today_count,
        "items": formatted_bookings
    }

# --- 4. Search Records (SECURED) ---
@router.get("/search-my-records") # SECURITY FIX: Removed provider_id from URL
def provider_record_search(
    q: str, 
    db: Session = Depends(get_db),
    current_provider: models.ServiceProvider = Depends(get_current_provider) # THE LOCK
):
    if len(q) < 2:
        return {"patients": [], "bookings": []}

    search_term = f"%{q}%"
    provider_id = current_provider.provider_id

    patients = db.query(models.User).join(models.Booking).filter(
        models.Booking.provider_id == provider_id,
        or_(
            models.User.name.ilike(search_term),
            models.User.phone.ilike(search_term)
        )
    ).distinct().all()

    bookings = db.query(models.Booking).filter(
        models.Booking.provider_id == provider_id,
        or_(
            models.Booking.booking_id.cast(String).ilike(search_term),
            models.Booking.order_notes.ilike(search_term)
        )
    ).limit(10).all()

    return {
        "patients": patients,
        "bookings": bookings
    }