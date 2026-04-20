# routers/providers.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, String
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from database import get_db
import models, schemas
from datetime import date, datetime, time, timedelta

# IMPORT OUR SECURITY ENGINE & BOUNCER
from dependencies import get_current_provider 

router = APIRouter(prefix="/providers", tags=["Service Providers"])

# ==========================================
# --- SECURITY MASKING FUNCTION ---
# ==========================================
def mask_sensitive_data(value: str, visible_chars: int = 4):
    """Safely masks bank accounts and IFSC codes (e.g. *******1234)"""
    if not value:
        return "Not Provided"
    if len(value) <= visible_chars:
        return value
    return "*" * (len(value) - visible_chars) + value[-visible_chars:]

# ==========================================
# --- SCHEMAS ---
# ==========================================
class ScheduleUpdate(BaseModel):
    day: str
    slots: List[str]

class ProviderLocationUpdate(BaseModel):
    latitude: float
    longitude: float

class BookingStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None 

# ==========================================
# --- 1. Dynamic Dashboard Data (Powers History & Earnings) ---
# ==========================================
@router.get("/dashboard/me") 
def get_provider_dashboard(
    db: Session = Depends(get_db),
    current_provider: models.ServiceProvider = Depends(get_current_provider) 
):
    provider_id = current_provider.provider_id

    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)
    
    current_month_start = today_start.replace(day=1)
    
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
    
    lifetime_earnings = 0
    this_month_earnings = 0

    for b in bookings:
        v_type = "Home Visit"
        if current_provider.provider_type == "Pharmacy":
            v_type = "Delivery"
        elif not b.delivery_address or str(b.delivery_address).lower() in ["none", "null", "", "platform default", "online", "undefined"]:
            v_type = "Video Consult"

        time_str = b.scheduled_time.strftime("%d %b, %I:%M %p") if b.scheduled_time else b.created_at.strftime("%d %b, ASAP")
        short_id = str(b.booking_id).split('-')[0].upper()
        
        status = b.booking_status.lower() if b.booking_status else "pending"

        # 🚨 THE FIX: Dynamically pull real booking price, fallback to 500 if missing
        booking_price = float(getattr(b, "price", 500.00))
        
        if status == "completed":
            lifetime_earnings += booking_price
            if b.created_at and b.created_at >= current_month_start:
                this_month_earnings += booking_price

        formatted_bookings.append({
            "booking_id": f"BKG-{short_id}",
            "raw_id": str(b.booking_id),
            "client_name": getattr(b, "patient_name", b.user.name if b.user else "Unknown Patient"),
            "client_phone": b.user.phone if b.user else "N/A",
            "age": getattr(b, "patient_age", "N/A"),
            "gender": getattr(b, "patient_gender", "N/A"),
            "visit_type": v_type,
            "time": time_str,
            "status": status,
            "address": b.delivery_address if v_type != "Video Consult" else "Online Video Room",
            "symptoms": getattr(b, "symptoms", getattr(b, "order_notes", "No additional notes provided.")),
            "price": booking_price 
        })

    return {
        "provider_info": {
            "name": current_provider.name,
            "type": current_provider.provider_type,
            "category": getattr(current_provider, "category", "General"),
            "bank_account_masked": mask_sensitive_data(current_provider.account_number),
            "ifsc_masked": mask_sensitive_data(current_provider.ifsc_code)
        },
        "total_today": today_count,
        "financials": {
            "lifetime_earnings": lifetime_earnings,
            "this_month_earnings": this_month_earnings,
            "current_month_name": date.today().strftime("%B") 
        },
        "items": formatted_bookings
    }

# ==========================================
# --- 2. Search Records ---
# ==========================================
@router.get("/search-my-records") 
def provider_record_search(
    q: str, 
    db: Session = Depends(get_db),
    current_provider: models.ServiceProvider = Depends(get_current_provider) 
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

# ==========================================
# --- 3. PUBLIC DIRECTORY ---
# ==========================================
@router.get("/all")
def get_all_providers(db: Session = Depends(get_db)):
    providers = db.query(models.ServiceProvider).filter(models.ServiceProvider.status == "approved").all()
    
    result = []
    for p in providers:
        result.append({
            "provider_id": p.provider_id,
            "name": p.name,
            "provider_type": p.provider_type,
            "category": getattr(p, "category", "General"),
            "profile_photo_url": p.profile_photo_url,
            "status": p.status
        })
    return result

# ==========================================
# --- 4. PROVIDER SAVES SCHEDULE ---
# ==========================================
@router.post("/schedule")
def update_provider_schedule(
    data: ScheduleUpdate, 
    db: Session = Depends(get_db), 
    current_provider: models.ServiceProvider = Depends(get_current_provider) 
):
    db.query(models.ProviderAvailability).filter(
        models.ProviderAvailability.provider_id == current_provider.provider_id,
        models.ProviderAvailability.day_of_week == data.day
    ).delete()

    for slot in data.slots:
        new_slot = models.ProviderAvailability(
            provider_id=current_provider.provider_id,
            day_of_week=data.day,
            time_slot=slot
        )
        db.add(new_slot)
    
    db.commit()
    return {"message": f"Successfully saved {len(data.slots)} slots for {data.day}"}

# ==========================================
# --- 5. PROVIDER FETCHES OWN SCHEDULE ---
# ==========================================
@router.get("/schedule/{day}")
def get_provider_schedule(
    day: str, 
    db: Session = Depends(get_db), 
    current_provider: models.ServiceProvider = Depends(get_current_provider) 
):
    availabilities = db.query(models.ProviderAvailability).filter(
        models.ProviderAvailability.provider_id == current_provider.provider_id,
        models.ProviderAvailability.day_of_week == day
    ).all()
    
    saved_slots = [a.time_slot for a in availabilities]
    return {"slots": saved_slots}

# ==========================================
# --- 6. UPDATE CLINIC GPS LOCATION ---
# ==========================================
@router.patch("/me/location")
def update_provider_location(
    data: ProviderLocationUpdate,
    db: Session = Depends(get_db),
    current_provider: models.ServiceProvider = Depends(get_current_provider)
):
    current_provider.latitude = data.latitude
    current_provider.longitude = data.longitude
    db.commit()
    
    return {"message": "Clinic GPS location updated successfully."}

# ==========================================
# --- 7. PATIENT FETCHES SLOTS ---
# ==========================================
@router.get("/{provider_id}/available-slots")
def get_available_slots(provider_id: str, date: str, db: Session = Depends(get_db)):
    try:
        start_of_day = datetime.strptime(date, "%Y-%m-%d")
        day_name = start_of_day.strftime("%A") 
        end_of_day = start_of_day + timedelta(days=1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format.")

    availabilities = db.query(models.ProviderAvailability).filter(
        models.ProviderAvailability.provider_id == provider_id,
        models.ProviderAvailability.day_of_week == day_name
    ).all()

    provider_slots = [a.time_slot for a in availabilities]

    if not provider_slots:
        provider_slots = [
            "09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", 
            "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM"
        ]

    existing_bookings = db.query(models.Booking).filter(
        models.Booking.provider_id == provider_id,
        models.Booking.scheduled_time >= start_of_day,
        models.Booking.scheduled_time < end_of_day,
        models.Booking.booking_status.in_(["pending", "confirmed"]) 
    ).all()

    taken_times = []
    for b in existing_bookings:
        if b.scheduled_time:
            taken_times.append(b.scheduled_time.strftime("%I:%M %p"))

    final_available_slots = []
    for slot in provider_slots:
        formatted_slot = slot.replace("0", "", 1) if slot.startswith("0") else slot
        if slot not in taken_times and formatted_slot not in taken_times:
            final_available_slots.append(slot)

    return final_available_slots

# ==========================================
# --- 8. COMPLETION & STATUS UPDATE ---
# ==========================================
@router.patch("/bookings/{booking_id}/status")
def update_provider_booking_status(
    booking_id: str,
    data: BookingStatusUpdate,
    db: Session = Depends(get_db),
    current_provider: models.ServiceProvider = Depends(get_current_provider) 
):
    booking = db.query(models.Booking).filter(
        models.Booking.booking_id == booking_id,
        models.Booking.provider_id == current_provider.provider_id
    ).first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.booking_status = data.status
    
    if data.notes:
        booking.symptoms = data.notes 

    db.commit()
    
    return {"message": f"Status updated to {data.status}"}

# ==========================================
# --- 9. MULTI-PROVIDER CATALOG ROUTING ---
# ==========================================
@router.post("/services")
def add_provider_service(
    data: Dict[str, Any], # 🚨 THE FIX: Safe Pydantic parsing!
    db: Session = Depends(get_db), 
    current_provider: models.ServiceProvider = Depends(get_current_provider)
):
    ptype = current_provider.provider_type
    
    if ptype == 'Doctor':
        validated_data = schemas.DoctorServiceCreate(**data).dict()
        new_item = models.DoctorService(provider_id=current_provider.provider_id, **validated_data)
        db.add(new_item)
    
    elif ptype == 'Pharmacy':
        med_data = schemas.MedicineCreate(**data).dict()
        new_med = models.Medicine(**med_data)
        db.add(new_med)
        db.flush() 
        
        new_item = models.PharmacyInventory(
            provider_id=current_provider.provider_id,
            medicine_id=new_med.medicine_id,
            price=data.get("price", 0),
            in_stock=True
        )
        db.add(new_item)
        
    elif ptype == 'Lab':
        test_data = schemas.LabTestCreate(**data).dict()
        new_test = models.LabTest(**test_data)
        db.add(new_test)
        db.flush() 
        
        new_item = models.LabOffering(
            provider_id=current_provider.provider_id,
            test_id=new_test.test_id,
            price=data.get("price", 0),
            home_collection_available=data.get("home_collection_available", False)
        )
        db.add(new_item)
        
    else:
        raise HTTPException(status_code=400, detail="Invalid provider type")

    db.commit()
    return {"message": "Service successfully added to catalog!"}

@router.get("/services/me")
def get_my_services(
    db: Session = Depends(get_db), 
    current_provider: models.ServiceProvider = Depends(get_current_provider)
):
    ptype = current_provider.provider_type
    
    if ptype == 'Doctor':
        return db.query(models.DoctorService).filter(models.DoctorService.provider_id == current_provider.provider_id).all()
    elif ptype == 'Pharmacy':
        return db.query(models.PharmacyInventory).options(joinedload(models.PharmacyInventory.medicine)).filter(models.PharmacyInventory.provider_id == current_provider.provider_id).all()
    elif ptype == 'Lab':
        return db.query(models.LabOffering).options(joinedload(models.LabOffering.test)).filter(models.LabOffering.provider_id == current_provider.provider_id).all()
    
    return []

# ==========================================
# --- 10. UPDATE PROFILE & BANK DETAILS ---
# ==========================================
@router.patch("/me")
def update_provider_profile(
    data: schemas.ProviderProfileUpdate,
    db: Session = Depends(get_db),
    current_provider: models.ServiceProvider = Depends(get_current_provider)
):
    """Updates the provider's Name, Detailed Bio, and Bank Info"""
    update_data = data.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(current_provider, key, value)
    
    db.commit()
    db.refresh(current_provider)
    
    return {
        "message": "Profile updated successfully!",
        "provider": {
            "name": current_provider.name,
            "phone": current_provider.phone,
            "address": current_provider.address,
            "bio": current_provider.bio,
            "bank_name": current_provider.bank_name,
            "account_number": current_provider.account_number,
            "ifsc_code": current_provider.ifsc_code,
            "profile_photo_url": current_provider.profile_photo_url
        }
    }