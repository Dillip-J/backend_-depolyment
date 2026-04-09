# routers/home.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
import models
from datetime import datetime, timezone
from math import radians, cos, sin, asin, sqrt
from typing import Optional, List

router = APIRouter(prefix="/home", tags=["Home & Search"])

# ==========================================
# Helper: GPS Distance Calculator (Haversine)
# ==========================================
def calculate_distance(lat1, lon1, lat2, lon2):
    try:
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            return float('inf')
        
        R = 6371.0 # Earth radius in km
        dlat = radians(float(lat2) - float(lat1))
        dlon = radians(float(lon2) - float(lon1))
        
        a = sin(dlat / 2)**2 + cos(radians(float(lat1))) * cos(radians(float(lat2))) * sin(dlon / 2)**2
        c = 2 * asin(sqrt(a))
        return R * c
    except (ValueError, TypeError):
        return float('inf')

# ==========================================
# Route 1: The Landing Page Dashboard
# ==========================================
@router.get("/")
def get_user_home(user_id: Optional[str] = None, db: Session = Depends(get_db)):
    # 1. Fetch Categories (Unique specialties from approved doctors)
    approved_docs = db.query(models.ServiceProvider).filter(
        models.ServiceProvider.status == 'approved',
        models.ServiceProvider.provider_type == 'Doctor'
    ).all()
    
    # Extract unique categories, default to 'General' if null
    categories = sorted(list(set([
        getattr(doc, 'category', 'General physician') or 'General physician' 
        for doc in approved_docs
    ])))

    # 2. Featured Providers (Showing a mix of Doctors/Labs/Pharmacies)
    featured_raw = db.query(models.ServiceProvider).filter(
        models.ServiceProvider.status == 'approved'
    ).limit(6).all()

    featured_list = []
    for f in featured_raw:
        featured_list.append({
            "id": str(f.provider_id),
            "name": f.name,
            "type": f.provider_type,
            "photo": f.profile_photo_url or "https://via.placeholder.com/150",
            "category": getattr(f, 'category', 'Healthcare Provider')
        })

    # 3. Active Booking Banner (For the specific user)
    active = None
    if user_id:
        try:
            active_booking = db.query(models.Booking).filter(
                models.Booking.user_id == user_id, 
                models.Booking.booking_status == 'confirmed',
                models.Booking.scheduled_time > datetime.now(timezone.utc)
            ).order_by(models.Booking.scheduled_time.asc()).first()
            
            if active_booking:
                provider = db.query(models.ServiceProvider).filter(
                    models.ServiceProvider.provider_id == active_booking.provider_id
                ).first()
                
                active = {
                    "booking_id": str(active_booking.booking_id),
                    "provider_name": provider.name if provider else "Healthcare Provider",
                    "time": active_booking.scheduled_time.strftime("%d %b, %H:%M")
                }
        except Exception:
            active = None # Don't crash the home page if booking query fails

    return {
        "categories": categories,
        "featured": featured_list,
        "active_booking": active
    }

# ==========================================
# Route 2: Location-Based Search Engine
# ==========================================
@router.get("/nearest")
def get_nearest_providers(
    lat: float = Query(0.0), 
    lon: float = Query(0.0), 
    category: str = "Doctor", 
    db: Session = Depends(get_db)
):
    # Fetch approved providers of the specific type
    providers = db.query(models.ServiceProvider).filter(
        models.ServiceProvider.provider_type == category,
        models.ServiceProvider.status == 'approved'
    ).all()

    results = []
    
    for p in providers:
        dist = calculate_distance(lat, lon, p.latitude, p.longitude)
        
        # Build Response Object
        p_dict = {
            "provider_id": str(p.provider_id),
            "name": p.name,
            "provider_type": p.provider_type,
            "category": getattr(p, 'category', 'General'), 
            "profile_photo_url": p.profile_photo_url or "https://via.placeholder.com/150",
            "distance_km": round(dist, 1) if dist != float('inf') else "Unknown",
            "price": float(getattr(p, 'price', 500)),
            "home_visit_charge": 200 if category == 'Doctor' else 0
        }

        # Calculate ETA (12 mins prep + 5 mins per km)
        if dist != float('inf'):
            eta = int(12 + (dist * 5))
            p_dict["eta_string"] = f"{eta}-{eta+10} mins"
            p_dict["delivery_charge"] = int(30 + (dist * 5))
        else:
            p_dict["eta_string"] = "45-60 mins"
            p_dict["delivery_charge"] = 50

        results.append((dist, p_dict))

    # Sort by distance
    results.sort(key=lambda x: x[0])
    
    return [item[1] for item in results]
# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session
# from database import get_db
# import models
# from datetime import datetime
# from math import radians, cos, sin, asin, sqrt

# router = APIRouter(prefix="/home", tags=["Home & Search"])

# # ==========================================
# # Helper: GPS Distance Calculator (Haversine)
# # ==========================================
# def calculate_distance(lat1, lon1, lat2, lon2):
#     if not all([lat1, lon1, lat2, lon2]):
#         return float('inf') # Push providers without GPS to the bottom
    
#     R = 6371.0 # Radius of the Earth in km
#     dlat = radians(float(lat2) - float(lat1))
#     dlon = radians(float(lon2) - float(lon1))
    
#     a = sin(dlat / 2)**2 + cos(radians(float(lat1))) * cos(radians(float(lat2))) * sin(dlon / 2)**2
#     c = 2 * asin(sqrt(a))
#     return R * c

# # ==========================================
# # Route 1: The Landing Page Dashboard
# # ==========================================
# @router.get("/")
# def get_user_home(user_id: str = None, db: Session = Depends(get_db)):
#     # 1. Categories (What types of doctors are available?)
#     # We look at the actual approved doctors in the DB and see what they specialize in
#     approved_docs = db.query(models.ServiceProvider).filter(
#         models.ServiceProvider.status == 'approved',
#         models.ServiceProvider.provider_type == 'Doctor'
#     ).all()
    
#     # Use a set to get unique categories (e.g., 'Cardiologist', 'General Physician')
#     # If they don't have a category saved, default to 'General'
#     categories = list(set([doc.category if hasattr(doc, 'category') and doc.category else 'General' for doc in approved_docs]))

#     # 2. Featured Providers (Show 6 randomly or the newest ones)
#     featured = db.query(models.ServiceProvider).filter(
#         models.ServiceProvider.status == 'approved'
#     ).limit(6).all()

#     # 3. Active Booking Banner (If user is logged in)
#     active = None
#     if user_id:
#         # Find their closest upcoming confirmed booking
#         active_booking = db.query(models.Booking).filter(
#             models.Booking.user_id == user_id, 
#             models.Booking.booking_status == 'confirmed',
#             models.Booking.scheduled_time > datetime.utcnow()
#         ).order_by(models.Booking.scheduled_time.asc()).first()
        
#         if active_booking:
#             # We need to know who the provider is
#             provider = db.query(models.ServiceProvider).filter(
#                 models.ServiceProvider.provider_id == active_booking.provider_id
#             ).first()
            
#             active = {
#                 "booking_id": str(active_booking.booking_id),
#                 "provider_name": provider.name if provider else "Unknown",
#                 "time": active_booking.scheduled_time.strftime("%d %b, %H:%M") if active_booking.scheduled_time else "ASAP"
#             }

#     return {
#         "categories": categories,
#         "featured": [
#             {
#                 "id": str(f.provider_id),
#                 "name": f.name,
#                 "type": f.provider_type,
#                 "photo": f.profile_photo_url
#             } for f in featured
#         ],
#         "active_booking": active
#     }

# # ==========================================
# # Route 2: Location-Based Search Engine
# # ==========================================
# @router.get("/nearest")
# def get_nearest_providers(lat: float = 0.0, lon: float = 0.0, category: str = "Doctor", db: Session = Depends(get_db)):
#     # 1. Fetch ALL APPROVED providers of the requested category
#     providers = db.query(models.ServiceProvider).filter(
#         models.ServiceProvider.provider_type == category,
#         models.ServiceProvider.status == 'approved'
#     ).all()

#     # 2. If the user didn't provide GPS (e.g., blocked location access), just return the list formatted
#     if lat == 0.0 and lon == 0.0:
#         return [
#             {
#                 "provider_id": str(p.provider_id),
#                 "name": p.name,
#                 "provider_type": p.provider_type,
#                 "specialty": p.category if hasattr(p, 'category') else "General",
#                 "profile_photo_url": p.profile_photo_url,
#                 "distance_km": None
#             } for p in providers
#         ]

#     # 3. If we have GPS, calculate the distance for each provider
#     provider_distances = []
#     for p in providers:
#         dist = calculate_distance(lat, lon, p.latitude, p.longitude)
        
#         # Convert to dictionary so we can inject the distance
#         p_dict = {
#             "provider_id": str(p.provider_id),
#             "name": p.name,
#             "provider_type": p.provider_type,
#             "specialty": p.category if hasattr(p, 'category') else "General",
#             "profile_photo_url": p.profile_photo_url,
#             "distance_km": round(dist, 1) if dist != float('inf') else None
#         }
#         provider_distances.append((dist, p_dict))

#     # 4. Sort by closest distance first
#     provider_distances.sort(key=lambda x: x[0])

#     # 5. Extract just the sorted dictionaries to send to the frontend
#     sorted_providers = [p[1] for p in provider_distances]
    
#     return sorted_providers

# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session, joinedload
# from database import get_db
# import models
# from typing import Optional
# from datetime import datetime

# router = APIRouter(prefix="/home", tags=["User Home"])

# @router.get("/")
# def get_user_home(user_id: Optional[int] = None, db: Session = Depends(get_db)):
#     response = {"categories": [], "featured": [], "active_booking": None}

#     # 1. Fetch Categories (using entities for performance)
#     categories = db.query(models.Service.category).distinct().all()
#     response["categories"] = [cat[0] for cat in categories if cat[0]]

#     # 2. Featured Services (limiting to 5 for a clean UI)
#     featured = db.query(models.Service).limit(5).all()
#     response["featured"] = featured

#     # 3. Personalized Active Booking Banner
#     if user_id:
#         # We use joinedload to fetch Service details in the SAME query
#         active = db.query(models.Booking)\
#             .options(joinedload(models.Booking.service))\
#             .filter(
#                 models.Booking.user_id == user_id,
#                 models.Booking.booking_status == 'confirmed',
#                 models.Booking.scheduled_time > datetime.now()
#             )\
#             .order_by(models.Booking.scheduled_time.asc())\
#             .first()

#         if active:
#             response["active_booking"] = {
#                 "booking_id": active.booking_id,
#                 "service_name": active.service.service_name, # Fast access!
#                 "scheduled_time": active.scheduled_time,
#                 "provider_name": active.provider.name if active.provider else None
#             }

#     return response