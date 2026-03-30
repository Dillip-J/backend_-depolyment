# routers/admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, String # <-- Fixed Imports
from database import get_db
import models
from uuid import UUID # <-- Needed for the provider_id fix

# IMPORT THE BOUNCER
from dependencies import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin Portal"])

# --- 1. Get Pending Queue ---
@router.get("/pending-applications")
def get_pending(
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin) # <-- THE LOCK
):
    return db.query(models.ServiceProvider).filter(models.ServiceProvider.status == "pending").all()


# --- 2. Approve a Provider ---
@router.patch("/approve/{provider_id}")
def approve_provider(
    provider_id: UUID, # <-- Fixed: Changed int to UUID
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin) # <-- THE LOCK
):
    provider = db.query(models.ServiceProvider).filter(models.ServiceProvider.provider_id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    provider.status = "approved"
    db.commit()
    return {"message": f"Successfully approved {provider.name}"}


# --- 3. Platform Stats ---
@router.get("/stats")
def get_platform_stats(
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin) # <-- THE LOCK
):
    return {
        "total_users": db.query(models.User).count(),
        "total_approved_providers": db.query(models.ServiceProvider).filter(models.ServiceProvider.status == "approved").count(),
        "total_bookings": db.query(models.Booking).count()
    }


# --- 4. Global Deep Search ---
@router.get("/global-admin-search")
def admin_deep_search(
    q: str, 
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin) # <-- THE LOCK
):
    search_term = f"%{q}%"

    users = db.query(models.User).filter(
        or_(
            models.User.name.ilike(search_term),
            models.User.email.ilike(search_term),
            models.User.phone.ilike(search_term)
        )
    ).all()

    providers = db.query(models.ServiceProvider).filter(
        or_(
            models.ServiceProvider.name.ilike(search_term),
            models.ServiceProvider.email.ilike(search_term),
            models.ServiceProvider.license_number.ilike(search_term)
        )
    ).all()

    bookings = db.query(models.Booking).filter(
        or_(
            models.Booking.booking_id.cast(String).ilike(search_term), # <-- Fixed: cast(String)
            models.Booking.booking_status.ilike(search_term)
        )
    ).limit(10).all()

    return {
        "results": {
            "users": users,
            "providers": providers,
            "bookings": bookings
        }
    }