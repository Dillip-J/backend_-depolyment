# routers/providers.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, String
from typing import List, Optional, Any, Dict
from database import get_db
import models, schemas
from datetime import date, datetime, time, timedelta
from dependencies import get_current_provider 

router = APIRouter(prefix="/providers", tags=["Service Providers"])

def mask_sensitive_data(value: str, visible_chars: int = 4):
    if not value: return "Not Provided"
    if len(value) <= visible_chars: return value
    return "*" * (len(value) - visible_chars) + value[-visible_chars:]

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
        v_type = "Video Consult" if str(b.delivery_address).lower() in ["none", "null", "", "online"] else "Home Visit"
        time_str = b.scheduled_time.strftime("%d %b, %I:%M %p") if b.scheduled_time else b.created_at.strftime("%d %b, ASAP")
        short_id = str(b.booking_id).split('-')[0].upper()
        status = b.booking_status.lower() if b.booking_status else "pending"

        booking_price = float(getattr(b, "total_amount") or 500.00)
        
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
            "flat_number": getattr(b, "flat_number", "Online"),
            "building_name": getattr(b, "building_name", "Online"),
            "landmark": getattr(b, "landmark", "Online"),
            "symptoms": getattr(b, "symptoms", "No symptoms provided."),
            "clinical_notes": getattr(b, "clinical_notes", ""), 
            "price": booking_price
        })

    # Calculate Exact Database Withdrawals
    withdrawals = db.query(models.Withdrawal).filter(models.Withdrawal.provider_id == provider_id).all()
    total_withdrawn = sum(float(w.amount) for w in withdrawals if w.status == 'completed')
    pending_withdrawn = sum(float(w.amount) for w in withdrawals if w.status == 'pending')
    
    available_balance = lifetime_earnings - total_withdrawn - pending_withdrawn

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
            "current_month_name": date.today().strftime("%B"),
            "total_withdrawn": total_withdrawn,
            "pending_withdrawal": pending_withdrawn,
            "available_balance": available_balance
        },
        "items": formatted_bookings
    }

# API Endpoint to officially request a withdrawal
@router.post("/withdraw")
def request_withdrawal(db: Session = Depends(get_db), current_provider: models.ServiceProvider = Depends(get_current_provider)):
    
    # 1. Make sure bank details exist
    if not current_provider.account_number or not current_provider.ifsc_code:
        raise HTTPException(status_code=400, detail="Bank details are missing. Please update your profile first.")

    # 2. Recalculate exact balance to prevent hacking
    bookings = db.query(models.Booking).filter(models.Booking.provider_id == current_provider.provider_id, models.Booking.booking_status == 'completed').all()
    lifetime_earnings = sum(float(b.total_amount or 500) for b in bookings)
    
    withdrawals = db.query(models.Withdrawal).filter(models.Withdrawal.provider_id == current_provider.provider_id).all()
    total_withdrawn = sum(float(w.amount) for w in withdrawals if w.status == 'completed')
    pending_withdrawn = sum(float(w.amount) for w in withdrawals if w.status == 'pending')
    
    available_balance = lifetime_earnings - total_withdrawn - pending_withdrawn
    
    if available_balance <= 0:
        raise HTTPException(status_code=400, detail="Insufficient funds. You have no available balance to withdraw.")

    # 3. Create the Transaction
    new_withdrawal = models.Withdrawal(
        provider_id=current_provider.provider_id,
        amount=available_balance,
        status='pending'
    )
    db.add(new_withdrawal)
    db.commit()
    
    return {"message": f"Success! Withdrawal of ₹{available_balance} initiated.", "withdrawn_amount": available_balance}

@router.get("/search-my-records") 
def provider_record_search(q: str, db: Session = Depends(get_db), current_provider: models.ServiceProvider = Depends(get_current_provider)):
    if len(q) < 2: return {"patients": [], "bookings": []}
    search_term = f"%{q}%"
    patients = db.query(models.User).join(models.Booking).filter(
        models.Booking.provider_id == current_provider.provider_id,
        or_(models.User.name.ilike(search_term), models.User.phone.ilike(search_term))
    ).distinct().all()
    bookings = db.query(models.Booking).filter(
        models.Booking.provider_id == current_provider.provider_id,
        models.Booking.booking_id.cast(String).ilike(search_term)
    ).limit(10).all()
    return {"patients": patients, "bookings": bookings}

@router.get("/all")
def get_all_providers(db: Session = Depends(get_db)):
    providers = db.query(models.ServiceProvider).filter(models.ServiceProvider.status == "approved").all()
    return [{
        "provider_id": p.provider_id,
        "name": p.name,
        "provider_type": p.provider_type,
        "category": getattr(p, "category", "General"),
        "profile_photo_url": p.profile_photo_url,
        "status": p.status
    } for p in providers]

# 🚨 FIX: Pointing to schemas.ScheduleUpdate
@router.post("/schedule")
def update_provider_schedule(data: schemas.ScheduleUpdate, db: Session = Depends(get_db), current_provider: models.ServiceProvider = Depends(get_current_provider)):
    db.query(models.ProviderAvailability).filter(
        models.ProviderAvailability.provider_id == current_provider.provider_id,
        models.ProviderAvailability.day_of_week == data.day
    ).delete()

    for slot in data.slots:
        db.add(models.ProviderAvailability(provider_id=current_provider.provider_id, day_of_week=data.day, time_slot=slot))
    db.commit()
    return {"message": f"Successfully saved {len(data.slots)} slots for {data.day}"}

@router.get("/schedule/{day}")
def get_provider_schedule(day: str, db: Session = Depends(get_db), current_provider: models.ServiceProvider = Depends(get_current_provider)):
    availabilities = db.query(models.ProviderAvailability).filter(
        models.ProviderAvailability.provider_id == current_provider.provider_id,
        models.ProviderAvailability.day_of_week == day
    ).all()
    return {"slots": [a.time_slot for a in availabilities]}

@router.get("/{provider_id}/available-slots")
def get_available_slots(provider_id: str, date: str, db: Session = Depends(get_db)):
    target_date = datetime.strptime(date, "%Y-%m-%d")
    schedule = db.query(models.ProviderAvailability).filter(
        models.ProviderAvailability.provider_id == provider_id,
        models.ProviderAvailability.day_of_week == target_date.strftime("%A")
    ).all()
    
    if not schedule: return []
    base_available_times = [s.time_slot for s in schedule] 

    active_bookings = db.query(models.Booking).filter(
        models.Booking.provider_id == provider_id,
        models.Booking.booking_status.in_(['pending', 'confirmed'])
    ).all()

    booked_time_strings = set()
    for b in active_bookings:
        if b.scheduled_time and b.scheduled_time.date() == target_date.date():
            booked_time_strings.add(b.scheduled_time.strftime("%I:%M %p"))

    final_slots = []
    for slot in base_available_times:
        try:
            if datetime.strptime(slot, "%I:%M %p").strftime("%I:%M %p") not in booked_time_strings:
                final_slots.append(slot)
        except ValueError:
            pass
    return final_slots

# 🚨 FIX: Pointing to schemas.BookingStatusUpdate
@router.patch("/bookings/{booking_id}/status")
def update_provider_booking_status(
    booking_id: str,
    data: schemas.BookingStatusUpdate,
    db: Session = Depends(get_db),
    current_provider: models.ServiceProvider = Depends(get_current_provider) 
):
    booking = db.query(models.Booking).filter(
        models.Booking.booking_id == booking_id,
        models.Booking.provider_id == current_provider.provider_id
    ).first()

    if not booking: raise HTTPException(status_code=404, detail="Booking not found")

    booking.booking_status = data.status
    if data.notes: booking.clinical_notes = data.notes 
    db.commit()
    return {"message": f"Status updated to {data.status}"}

@router.post("/services")
def add_provider_service(data: Dict[str, Any], db: Session = Depends(get_db), current_provider: models.ServiceProvider = Depends(get_current_provider)):
    if current_provider.provider_type == 'Doctor':
        validated_data = schemas.DoctorServiceCreate(**data).dict()
        db.add(models.DoctorService(provider_id=current_provider.provider_id, **validated_data))
        db.commit()
        return {"message": "Service successfully added to catalog!"}
    raise HTTPException(status_code=400, detail="Invalid provider type")

@router.get("/services/me")
def get_my_services(db: Session = Depends(get_db), current_provider: models.ServiceProvider = Depends(get_current_provider)):
    if current_provider.provider_type == 'Doctor':
        return db.query(models.DoctorService).filter(models.DoctorService.provider_id == current_provider.provider_id).all()
    return []

@router.delete("/services/{item_id}")
def delete_catalog_item(item_id: int, db: Session = Depends(get_db), current_provider: models.ServiceProvider = Depends(get_current_provider)):
    if current_provider.provider_type == 'Doctor':
        if db.query(models.DoctorService).filter(models.DoctorService.service_id == item_id, models.DoctorService.provider_id == current_provider.provider_id).delete() > 0:
            db.commit()
            return {"message": "Service deleted"}
    raise HTTPException(status_code=404, detail="Service not found.")

@router.get("/me")
def get_provider_profile(current_provider: models.ServiceProvider = Depends(get_current_provider)):
    return current_provider

@router.patch("/me")
def update_provider_profile(data: schemas.ProviderProfileUpdate, db: Session = Depends(get_db), current_provider: models.ServiceProvider = Depends(get_current_provider)):
    for key, value in data.dict(exclude_unset=True).items():
        setattr(current_provider, key, value)
    db.commit()
    db.refresh(current_provider)
    return {"message": "Profile updated successfully!", "provider": current_provider}