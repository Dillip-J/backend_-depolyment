#models.py
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, DateTime, Text, Numeric
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import uuid

class User(Base):
    __tablename__ = "users"
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    phone = Column(String)
    bookings = relationship("Booking", back_populates="user")

class Service(Base):
    __tablename__ = "services"
    service_id = Column(BigInteger, primary_key=True, index=True)
    service_name = Column(String, nullable=False)
    category = Column(String)
    base_price = Column(Numeric(10, 2))

class ProviderService(Base):
    __tablename__ = "provider_services"
    provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.provider_id"), primary_key=True)
    service_id = Column(BigInteger, ForeignKey("services.service_id"), primary_key=True)
    price = Column(Numeric(10, 2))
    status = Column(String)
    provider = relationship("ServiceProvider")

class Booking(Base):
    __tablename__ = "bookings"
    booking_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)    
    # 2. Update the Foreign Keys to expect UUIDs
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.provider_id"), nullable=False)
    service_id = Column(BigInteger, ForeignKey("services.service_id"))
    scheduled_time = Column(DateTime, nullable=False)
    booking_status = Column(String, default="pending")
    
    user = relationship("User", back_populates="bookings")
    service = relationship("Service")
    provider = relationship("ServiceProvider")

class MedicalRecord(Base):
    __tablename__ = "medical_records"
    record_id = Column(BigInteger, primary_key=True)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.booking_id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.provider_id"))
    diagnosis = Column(Text)
    report_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    booking = relationship("Booking")
    provider = relationship("ServiceProvider")

class Admin(Base):
    __tablename__ = "admins"
    admin_id = Column(BigInteger, primary_key=True)
    name = Column(String)
    email = Column(String)
    role = Column(String)

class ServiceProvider(Base):
    __tablename__ = "service_providers"
    provider_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    provider_type = Column(String, nullable=False) # 'Doctor', 'Lab', 'Pharmacy'
    category = Column(String)
    license_number = Column(String)
    status = Column(String, default="pending")
    # latitude and longitude for manual search and real-time tracking (for deliveries)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    address = Column(Text) # Physical address for manual search
    # profile photo and license document URLs for better provider profiles and admin verification
    profile_photo_url = Column(String, nullable=True)
    license_document_url = Column(String, nullable=True)

class Review(Base):
    __tablename__ = "reviews"
    review_id = Column(BigInteger, primary_key=True, index=True)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.booking_id"), unique=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)

    booking = relationship("Booking")

class Complaint(Base):
    __tablename__ = "complaints"
    complaint_id = Column(BigInteger, primary_key=True, index=True)
    booking_id = Column(UUID(as_uuid=True),ForeignKey("bookings.booking_id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.provider_id"))
    complaint_text = Column(Text, nullable=False)
    status = Column(String, default="open") # open, resolved

# --- The "Menu" System for Labs and Pharmacies ---

class CatalogItem(Base):
    __tablename__ = "catalog_items"
    # A global list of everything that can be bought
    item_id = Column(BigInteger, primary_key=True, index=True)
    item_name = Column(String, nullable=False) # e.g., "Paracetamol 500mg" or "Thyroid Panel"
    item_type = Column(String, nullable=False) # 'Medicine' or 'LabTest'
    category = Column(String) # e.g., 'Painkillers', 'Blood Work'
    description = Column(Text)

class ProviderInventory(Base):
    __tablename__ = "provider_inventory"
    # The Bridge: Links a specific Pharmacy/Lab to an item on the Menu
    inventory_id = Column(BigInteger, primary_key=True, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.provider_id"))
    item_id = Column(BigInteger, ForeignKey("catalog_items.item_id"))
    
    # Each pharmacy/lab sets their own price and stock status
    price = Column(Numeric(10, 2), nullable=False)
    in_stock = Column(Integer, default=1) # 1 for True (In Stock), 0 for False
    
    provider = relationship("ServiceProvider")
    item = relationship("CatalogItem")

class SavedAddress(Base):
    __tablename__ = "saved_addresses"
    address_id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    label = Column(String(50), nullable=False) # e.g., 'Home', 'Office'
    address_text = Column(Text, nullable=False)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    is_default = Column(Integer, default=0) # 1 for True, 0 for False
    
    user = relationship("User", backref="saved_addresses")
