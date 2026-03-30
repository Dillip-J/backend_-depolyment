# routers/services.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from database import get_db
import models
from uuid import UUID

# IMPORT THE BOUNCER
from dependencies import get_current_provider

router = APIRouter(prefix="/services", tags=["Services & Catalog"])

# ==========================================
# 1. PUBLIC ROUTES (For Patients to Browse)
# ==========================================

@router.get("/catalog/{item_type}")
def get_global_catalog(item_type: str, db: Session = Depends(get_db)):
    """
    Fetches the global list of items. 
    item_type can be: 'Medicine', 'LabTest', or 'DoctorService'
    """
    if item_type == "DoctorService":
        return db.query(models.Service).all()
    else:
        return db.query(models.CatalogItem).filter(models.CatalogItem.item_type == item_type).all()


@router.get("/provider/{provider_id}/menu")
def get_provider_menu(provider_id: UUID, db: Session = Depends(get_db)):
    """Fetches exactly what a specific Doctor, Pharmacy, or Lab is selling."""
    provider = db.query(models.ServiceProvider).filter(models.ServiceProvider.provider_id == provider_id).first()
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    if provider.provider_type == "Doctor":
        # Get doctor's specific services and prices
        services = db.query(models.ProviderService)\
            .options(joinedload(models.ProviderService.service))\
            .filter(models.ProviderService.provider_id == provider_id).all()
        return {"provider_type": "Doctor", "menu": services}
        
    else:
        # Get Pharmacy or Lab inventory
        inventory = db.query(models.ProviderInventory)\
            .options(joinedload(models.ProviderInventory.item))\
            .filter(models.ProviderInventory.provider_id == provider_id).all()
        return {"provider_type": provider.provider_type, "menu": inventory}


# ==========================================
# 2. SECURE PROVIDER ROUTES (For Doctors/Pharmacies to set prices)
# ==========================================

@router.post("/me/add-inventory")
def add_item_to_my_menu(
    item_id: int, 
    price: float, 
    db: Session = Depends(get_db),
    current_provider: models.ServiceProvider = Depends(get_current_provider) # <-- THE LOCK
):
    """Allows a logged-in provider to add an item to their menu and set a price."""
    
    if price < 0:
        raise HTTPException(status_code=400, detail="Price cannot be negative.")
        
    # If it's a doctor, add to ProviderService table
    if current_provider.provider_type == "Doctor":
        existing = db.query(models.ProviderService).filter_by(
            provider_id=current_provider.provider_id, service_id=item_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="You already offer this service.")
            
        new_service = models.ProviderService(
            provider_id=current_provider.provider_id,
            service_id=item_id,
            price=price,
            status="active"
        )
        db.add(new_service)
        
    # If it's a Pharmacy or Lab, add to ProviderInventory table
    else:
        existing = db.query(models.ProviderInventory).filter_by(
            provider_id=current_provider.provider_id, item_id=item_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Item already in your inventory.")
            
        new_item = models.ProviderInventory(
            provider_id=current_provider.provider_id,
            item_id=item_id,
            price=price,
            in_stock=1
        )
        db.add(new_item)
        
    db.commit()
    return {"message": "Successfully added to your menu!"}


@router.patch("/me/update-doctor-price/{service_id}")
def update_doctor_price(
    service_id: int,
    price: float,
    db: Session = Depends(get_db),
    current_provider: models.ServiceProvider = Depends(get_current_provider) # <-- THE LOCK
):
    """Allows DOCTORS to update the price of a service they offer."""
    if current_provider.provider_type != "Doctor":
        raise HTTPException(status_code=400, detail="Only doctors can use this route.")
        
    if price < 0:
        raise HTTPException(status_code=400, detail="Price cannot be negative.")

    link = db.query(models.ProviderService).filter(
        models.ProviderService.provider_id == current_provider.provider_id,
        models.ProviderService.service_id == service_id
    ).first()

    if not link:
        raise HTTPException(status_code=404, detail="You don't currently offer this service.")

    link.price = price
    db.commit()
    
    return {"message": "Your personal pricing has been updated successfully!"}


@router.patch("/me/update-inventory/{inventory_id}")
def update_inventory_status(
    inventory_id: int,
    price: float = None,
    in_stock: int = None, # 1 for yes, 0 for no
    db: Session = Depends(get_db),
    current_provider: models.ServiceProvider = Depends(get_current_provider) # <-- THE LOCK
):
    """Allows PHARMACIES/LABS to quickly mark a medicine as Out of Stock or change price."""
    
    if current_provider.provider_type == "Doctor":
        raise HTTPException(status_code=400, detail="Doctors must use the /update-doctor-price route.")
        
    if price is not None and price < 0:
        raise HTTPException(status_code=400, detail="Price cannot be negative.")
        
    # Security: Ensure they can only edit their OWN inventory
    inventory = db.query(models.ProviderInventory).filter(
        models.ProviderInventory.inventory_id == inventory_id,
        models.ProviderInventory.provider_id == current_provider.provider_id
    ).first()
    
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory item not found in your catalog.")
        
    if price is not None:
        inventory.price = price
    if in_stock is not None:
        inventory.in_stock = in_stock
        
    db.commit()
    return {"message": "Inventory updated successfully"}
# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session
# from database import get_db
# import models

# router = APIRouter(prefix="/support", tags=["Support"])

# @router.get("/")
# def get_support(db: Session = Depends(get_db)):
#     # Fetch admins with the 'support' role
#     staff = db.query(models.Admin).filter(models.Admin.role == "support").all()
    
#     return {
#         "header": "Help & Support",
#         "contacts": [
#             {"name": s.name, "email": s.email} 
#             for s in staff
#         ],
#         "faqs": [
#             {"q": "How to cancel a booking?", "a": "Go to the Bookings tab and select Cancel."},
#             {"q": "How to view reports?", "a": "Navigate to the Medical Records section."}
#         ]
#     }
# from fastapi import APIRouter, Depends, Query
# from sqlalchemy.orm import Session
# from database import get_db
# from typing import Optional, List

# # CORRECTED: Import directly from the files to avoid the "models" loop
# from routers.services import Service, ServiceProvider, ProviderService

# router = APIRouter(prefix="/services", tags=["Search Page"])

# @router.get("/")
# def search_services(
#     category: Optional[str] = Query(None),
#     search: Optional[str] = Query(None),
#     db: Session = Depends(get_db)
# ):
#     # Start a base query
#     query = db.query(Service)

#     # Dynamically add filters
#     if category:
#         query = query.filter(Service.category.ilike(f"%{category}%"))
#     if search:
#         query = query.filter(Service.service_name.ilike(f"%{search}%"))

#     return query.all()

# @router.get("/{service_id}/providers")
# def get_providers(service_id: int, db: Session = Depends(get_db)):
#     """List providers offering this specific service."""
#     # We query the bridge table (ProviderService) to get the prices
#     results = db.query(ProviderService).filter(ProviderService.service_id == service_id).all()
    
#     # Format the response to include provider details via relationship
#     return [
#         {
#             "provider_id": item.provider.provider_id,
#             "name": item.provider.name,
#             "provider_type": item.provider.provider_type,
#             "price": item.price,
#             "status": item.status
#         }
#         for item in results
#     ]