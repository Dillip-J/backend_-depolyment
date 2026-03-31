# # schemas.py
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator, model_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# ==========================================
# AUTHENTICATION TOKENS (JWT)
# ==========================================
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[UUID] = None
    role: Optional[str] = None # e.g., 'user', 'Doctor', 'Pharmacy'

# ==========================================
# AUTHENTICATION SCHEMAS
# ==========================================
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ProviderCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    provider_type: str # 'Doctor', 'Pharmacy', 'Lab'
    phone: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    # We don't usually accept file URLs directly on signup, they upload files AFTER signup,
    # but we can leave these here if your frontend sends them.
    profile_photo_url: Optional[str] = None
    license_document_url: Optional[str] = None

class ProviderLogin(BaseModel):
    email: EmailStr
    password: str

class ProviderResponse(ORMBase):
    provider_id: UUID
    name: str
    provider_type: str
    status: str
    profile_photo_url: Optional[str] = None

# ==========================================
# THE 3 DOMAINS: DOCTORS, PHARMACIES, LABS
# ==========================================

# --- 1. Doctors ---
class DoctorServiceCreate(BaseModel):
    service_name: str
    description: Optional[str] = None
    price: float

    @field_validator('price')
    @classmethod
    def price_must_be_positive(cls, v):
        if v < 0:
            raise ValueError('Price cannot be negative.')
        return v

class DoctorServiceResponse(ORMBase):
    service_id: int
    service_name: str
    price: Decimal

# --- 2. Pharmacies (Medicines & Inventory) ---
class MedicineCreate(BaseModel):
    medicine_name: str
    manufacturer: Optional[str] = None
    requires_prescription: bool = False
    description: Optional[str] = None

class MedicineResponse(ORMBase):
    medicine_id: int
    medicine_name: str
    requires_prescription: bool

class PharmacyInventoryCreate(BaseModel):
    medicine_id: int
    price: float
    in_stock: bool = True

class PharmacyInventoryResponse(ORMBase):
    inventory_id: int
    price: Decimal
    in_stock: bool
    medicine: MedicineResponse # Nests the medicine details

# --- 3. Labs (Tests & Offerings) ---
class LabTestCreate(BaseModel):
    test_name: str
    category: Optional[str] = None
    description: Optional[str] = None

class LabTestResponse(ORMBase):
    test_id: int
    test_name: str
    category: Optional[str]

class LabOfferingCreate(BaseModel):
    test_id: int
    price: float
    home_collection_available: bool = False

# ==========================================
# BOOKINGS & TRANSACTIONS
# ==========================================
class BookingCreate(BaseModel):
    # We remove user_id from here! The Bouncer (JWT) will provide the user_id securely.
    provider_id: UUID
    
    doctor_service_id: Optional[int] = None
    medicine_id: Optional[int] = None
    lab_test_id: Optional[int] = None
    
    scheduled_time: Optional[datetime] = None
    delivery_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    order_notes: Optional[str] = None

    # --- NEW: MULTI-PATIENT / OVERRIDE FIELDS ---
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    symptoms: Optional[str] = None

    @model_validator(mode='after')
    def check_exclusive_service(self):
        # Count how many of the service IDs actually have a value
        provided_services = [
            bool(self.doctor_service_id), 
            bool(self.medicine_id), 
            bool(self.lab_test_id)
        ]
        
        if sum(provided_services) > 1:
            raise ValueError("A booking cannot mix Doctors, Medicines, and Labs. Please select only ONE service type.")
        if sum(provided_services) == 0:
            raise ValueError("You must select at least one service, medicine, or lab test to book.")
            
        return self
        
class BookingResponse(ORMBase):
    booking_id: UUID
    booking_status: str
    scheduled_time: Optional[datetime]
    # In a full app, you would nest the user and provider details here too

# ==========================================
# SAVED ADDRESSES
# ==========================================
class SavedAddressCreate(BaseModel):
    label: str
    address_text: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: bool = False

class SavedAddressResponse(ORMBase):
    address_id: int
    label: str
    address_text: str
    latitude: Optional[float]
    longitude: Optional[float]
    is_default: bool

# ==========================================
# FEEDBACK & RECORDS
# ==========================================

# --- Medical Records ---
class MedicalRecordCreate(BaseModel):
    booking_id: UUID
    diagnosis: str
    report_url: Optional[str] = None

class MedicalRecordResponse(ORMBase):
    record_id: int
    booking_id: UUID
    diagnosis: str
    report_url: Optional[str]

# --- Reviews ---
class ReviewCreate(BaseModel):
    booking_id: UUID
    rating: int 
    comment: Optional[str] = None

class ReviewOut(ReviewCreate, ORMBase):
    review_id: UUID
    created_at: Optional[datetime] = None

# --- Complaints ---
class ComplaintCreate(BaseModel):
    booking_id: UUID
    complaint_text: str
    # Security: We removed user_id and provider_id. 
    # The Bouncer provides user_id, and the database provides provider_id.

class ComplaintOut(ComplaintCreate, ORMBase):
    complaint_id: UUID
    user_id: UUID
    provider_id: UUID
    status: str
    created_at: Optional[datetime] = None

class UserOut(BaseModel):
    user_id: str
    name: str
    email: str

    class Config:
        from_attributes = True  # For Pydantic v2
        orm_mode = True         # For Pydantic v1
    
# from pydantic import BaseModel, EmailStr, ConfigDict
# from typing import Optional, List
# from datetime import datetime
# from decimal import Decimal

# # --- Base Schema with ORM Config ---
# class ORMBase(BaseModel):
#     model_config = ConfigDict(from_attributes=True)

# # --- User Auth ---
# class UserCreate(BaseModel):
#     name: str
#     email: EmailStr
#     password: str
#     phone: Optional[str] = None

# class UserLogin(BaseModel):
#     email: EmailStr
#     password: str

# class UserResponse(ORMBase):
#     user_id: int
#     name: str
#     email: str
#     phone: Optional[str]

# # --- Booking ---
# class BookingCreate(BaseModel):
#     user_id: int
#     provider_id: int
#     service_id: int
#     scheduled_time: datetime

# class BookingResponse(ORMBase):
#     booking_id: int
#     scheduled_time: datetime
#     booking_status: str
#     # We can include nested data from relationships here
#     service_name: Optional[str] = None 
#     provider_name: Optional[str] = None

# # --- Feedback ---
# class ReviewCreate(BaseModel):
#     booking_id: int
#     rating: int
#     comment: Optional[str] = None

# class ComplaintCreate(BaseModel):
#     booking_id: int
#     user_id: int
#     provider_id: int
#     complaint_text: str

# # --- Home & Search (New) ---
# class ServiceResponse(ORMBase):
#     service_id: int
#     service_name: str
#     category: str
#     base_price: Decimal

# class HomePageResponse(BaseModel):
#     categories: List[str]
#     featured: List[ServiceResponse]
#     active_booking: Optional[BookingResponse] = None