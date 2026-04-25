# routers/home.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
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
    # 1. Categories (What types of doctors are available?)
    approved_docs = db.query(models.ServiceProvider).filter(
        models.ServiceProvider.status == 'approved',
        models.ServiceProvider.provider_type == 'Doctor'
    ).all()
    
    categories = list(set([doc.category if hasattr(doc, 'category') and doc.category else 'General' for doc in approved_docs]))

    # 2. Featured Providers
    featured = db.query(models.ServiceProvider).filter(
        models.ServiceProvider.status == 'approved'
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
# Route 2: Location-Based Search Engine (ETA & Dynamic Pricing)
# ==========================================
@router.get("/nearest")
def get_nearest_providers(lat: float = 0.0, lon: float = 0.0, category: str = "Doctor", db: Session = Depends(get_db)):
    # 1. Fetch ALL APPROVED providers of the requested category
    providers = db.query(models.ServiceProvider).filter(
        models.ServiceProvider.provider_type == category,
        models.ServiceProvider.status == 'approved'
    ).all()

    provider_distances = []
    
    for p in providers:
        # Calculate distance
        dist = calculate_distance(lat, lon, p.latitude, p.longitude) if lat != 0.0 else float('inf')
        is_valid_dist = dist != float('inf')

        # Base dictionary mapping database models to JS frontend keys
        p_dict = {
            "provider_id": str(p.provider_id),
            "name": p.name,
            "provider_type": p.provider_type,
            "category": getattr(p, 'category', 'General'), 
            
            # 🚨 THE MISSING DATA FIX: Attach Bio, Phone, and GPS Coordinates
            "bio": getattr(p, "bio", "No description provided by this professional."),
            "phone": getattr(p, "phone", "Contact not available"),
            "latitude": getattr(p, "latitude", None),
            "longitude": getattr(p, "longitude", None),
            
            # 🚨 THE PHOTO FIX IS SAFELY APPLIED HERE:
            "profile_photo_url": getattr(p, "profile_photo_url", None),
            
            "distance_km": round(dist, 1) if is_valid_dist else "Unknown",
            
            # Base Doctor/Lab Pricing (Defaults)
            "price": getattr(p, 'price', 500) if category == 'Doctor' else getattr(p, 'price', 45),
            "home_visit_charge": 200,
        }

        # Dynamic ETA and Variable Delivery Pricing Logic
        if is_valid_dist:
            # 10 mins base prep + 4 mins per km
            eta_mins = int(10 + (dist * 4))
            p_dict["eta_string"] = f"{eta_mins} - {eta_mins + 15} mins"
            # Delivery: Base ₹30 + ₹5 per km
            p_dict["delivery_charge"] = int(30 + (dist * 5))
            # Lab Collection: Base ₹10 + ₹2 per km
            p_dict["home_collection_charge"] = int(10 + (dist * 2))
        else:
            # Safe Fallbacks if User blocked GPS or Provider has no GPS
            p_dict["eta_string"] = "45 - 60 mins"
            p_dict["delivery_charge"] = 50
            p_dict["home_collection_charge"] = 15

        provider_distances.append((dist, p_dict))

    # Sort by closest distance first
    provider_distances.sort(key=lambda x: x[0])

    # Extract just the sorted dictionaries to send to the frontend
    sorted_providers = [p[1] for p in provider_distances]
    
    return sorted_providers