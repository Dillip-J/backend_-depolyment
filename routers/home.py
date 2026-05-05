# routers/home.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from database import get_db
import models
from datetime import datetime
from math import radians, cos, sin, asin, sqrt

router = APIRouter(prefix="/home", tags=["Home & Search"])

# ==========================================
# Helper: GPS Distance Calculator (Haversine)
# ==========================================
def calculate_distance(lat1, lon1, lat2, lon2):
    if not all([lat1, lon1, lat2, lon2]):
        return float('inf') # Push providers without GPS to the bottom
    
    R = 6371.0 # Radius of the Earth in km
    dlat = radians(float(lat2) - float(lat1))
    dlon = radians(float(lon2) - float(lon1))
    
    a = sin(dlat / 2)**2 + cos(radians(float(lat1))) * cos(radians(float(lat2))) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    return R * c

# ==========================================
# Route 1: The Landing Page Dashboard
# ==========================================
@router.get("/")
def get_user_home(user_id: str = None, db: Session = Depends(get_db)):
    # 1. Categories
    approved_docs = db.query(models.ServiceProvider).filter(
        models.ServiceProvider.status.ilike('approved'),
        models.ServiceProvider.provider_type.ilike('doctor')
    ).all()
    
    categories = list(set([doc.category if hasattr(doc, 'category') and doc.category else 'General' for doc in approved_docs]))

    # 2. Featured Providers
    featured = db.query(models.ServiceProvider).filter(
        models.ServiceProvider.status.ilike('approved')
    ).limit(6).all()

    # 3. Active Booking Banner
    active = None
    if user_id:
        active_booking = db.query(models.Booking).filter(
            models.Booking.user_id == user_id, 
            models.Booking.booking_status == 'confirmed',
            or_(
                models.Booking.scheduled_time > datetime.utcnow(),
                models.Booking.scheduled_time == None
            )
        ).order_by(models.Booking.created_at.asc()).first() 
        
        if active_booking:
            provider = db.query(models.ServiceProvider).filter(
                models.ServiceProvider.provider_id == active_booking.provider_id
            ).first()
            
            active = {
                "booking_id": str(active_booking.booking_id),
                "provider_name": provider.name if provider else "Unknown",
                "time": active_booking.scheduled_time.strftime("%d %b, %H:%M") if active_booking.scheduled_time else "ASAP"
            }

    return {
        "categories": categories,
        "featured": [
            {
                "id": str(f.provider_id),
                "name": f.name,
                "type": f.provider_type,
                "photo": getattr(f, "profile_photo_url", None)
            } for f in featured
        ],
        "active_booking": active
    }

# ==========================================
# Route 2: Location-Based Search Engine 
# ==========================================
@router.get("/nearest")
def get_nearest_providers(lat: float = Query(0.0), lon: float = Query(0.0), category: str = Query(None), db: Session = Depends(get_db)):
    
    query = db.query(models.ServiceProvider).options(
        joinedload(models.ServiceProvider.doctor_services)
    ).filter(models.ServiceProvider.status.ilike('approved'))

    if category:
        query = query.filter(
            (models.ServiceProvider.provider_type.ilike(f"%{category}%")) | 
            (models.ServiceProvider.category.ilike(f"%{category}%"))
        )

    providers = query.all()
    provider_distances = []
    
    for p in providers:
        dist = calculate_distance(lat, lon, p.latitude, p.longitude) if lat != 0.0 else float('inf')
        is_valid_dist = dist != float('inf')

        # 🚨 FIX: Explicitly send the exact consultation_fee from the database!
        base_fee = float(getattr(p, 'consultation_fee', 500.0))

        p_dict = {
            "provider_id": str(p.provider_id),
            "name": p.name,
            "provider_type": p.provider_type,
            "category": getattr(p, 'category', 'General'), 
            "bio": getattr(p, "bio", "No description provided by this professional."),
            "phone": getattr(p, "phone", "Contact not available"),
            "latitude": getattr(p, "latitude", None),
            "longitude": getattr(p, "longitude", None),
            "profile_photo_url": getattr(p, "profile_photo_url", None),
            "distance_km": round(dist, 1) if is_valid_dist else "Unknown",
            "consultation_fee": base_fee, # 🚨 Sent explicitly so JS doesn't guess
            "price": base_fee, # Duplicate for backward compatibility
            "home_visit_charge": 200, 
        }

        services = getattr(p, "doctor_services", [])
        if services:
            p_dict["doctor_services"] = [
                {"service_name": s.service_name, "price": float(s.price)} for s in services
            ]

        if is_valid_dist:
            eta_mins = int(10 + (dist * 4))
            p_dict["eta_string"] = f"{eta_mins} - {eta_mins + 15} mins"
        else:
            p_dict["eta_string"] = "45 - 60 mins"

        provider_distances.append((dist, p_dict))

    provider_distances.sort(key=lambda x: x[0])
    return [p[1] for p in provider_distances]

# ==========================================
# Route 3: Global Text Search
# ==========================================
@router.get("/search")
def global_search(q: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    search_term = f"%{q}%"
    
    doctors = db.query(models.ServiceProvider).filter(
        models.ServiceProvider.status == 'approved',
        models.ServiceProvider.provider_type == 'Doctor',
        (models.ServiceProvider.name.ilike(search_term)) | (models.ServiceProvider.category.ilike(search_term))
    ).limit(5).all()

    return {
        "doctors": [{"provider_id": str(d.provider_id), "name": d.name, "category": getattr(d, "category", "General")} for d in doctors]
    }