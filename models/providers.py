# models/providers.py
from sqlalchemy import Column, String, BigInteger, Boolean, Numeric, Text, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid

class ServiceProvider(Base):
    __tablename__ = "service_providers"
    
    provider_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_type = Column(String(50), nullable=False) # 'Doctor', 'Pharmacy', 'Lab'
    name = Column(String(255), nullable=False)
    
    # 🚨 ADDED: Category column for Patient Search Filtering
    category = Column(String(100), nullable=True) # e.g., Cardiologist, General Physician
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    phone = Column(String(20))
    address = Column(Text)
    
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    
    status = Column(String(50), default='pending')
    background_verification = Column(String(50), default='pending')
    profile_photo_url = Column(String(500))
    license_document_url = Column(String(500))

    # Relationships
    doctor_services = relationship("DoctorService", back_populates="provider", cascade="all, delete")
    bookings = relationship("Booking", back_populates="provider")
    # Add relationships for labs and pharmacies if you want to navigate from provider -> inventory
    pharmacy_inventory = relationship("PharmacyInventory", back_populates="provider", cascade="all, delete")
    lab_offerings = relationship("LabTestOffering", back_populates="provider", cascade="all, delete")

class ProviderAvailability(Base):
    __tablename__ = "provider_availability"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.provider_id", ondelete="CASCADE"))
    day_of_week = Column(String) # e.g., "Monday"
    time_slot = Column(String)   # e.g., "10:00 AM"

class DoctorService(Base):
    __tablename__ = "doctor_services"
    
    service_id = Column(BigInteger, primary_key=True, autoincrement=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.provider_id", ondelete="CASCADE"), nullable=False)
    
    service_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False) 
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), default='active')

    provider = relationship("ServiceProvider", back_populates="doctor_services")
    bookings = relationship("Booking", back_populates="doctor_service")

# --- PHARMACY DOMAIN ---
class Medicine(Base):
    __tablename__ = "medicines"
    medicine_id = Column(BigInteger, primary_key=True, autoincrement=True)
    medicine_name = Column(String(255), nullable=False)
    manufacturer = Column(String(255))
    requires_prescription = Column(Boolean, default=False)
    description = Column(Text)

class PharmacyInventory(Base):
    __tablename__ = "pharmacy_inventory"
    inventory_id = Column(BigInteger, primary_key=True, autoincrement=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.provider_id", ondelete="CASCADE"), nullable=False)
    medicine_id = Column(BigInteger, ForeignKey("medicines.medicine_id", ondelete="CASCADE"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    in_stock = Column(Boolean, default=True)

    provider = relationship("ServiceProvider", back_populates="pharmacy_inventory")
    medicine = relationship("Medicine")

# --- LAB DOMAIN ---
class LabTest(Base):
    __tablename__ = "lab_tests"
    test_id = Column(BigInteger, primary_key=True, autoincrement=True)
    test_name = Column(String(255), nullable=False)
    category = Column(String(100))
    description = Column(Text)

class LabTestOffering(Base):
    __tablename__ = "lab_test_offerings"
    offering_id = Column(BigInteger, primary_key=True, autoincrement=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.provider_id", ondelete="CASCADE"), nullable=False)
    test_id = Column(BigInteger, ForeignKey("lab_tests.test_id", ondelete="CASCADE"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    home_collection_available = Column(Boolean, default=False)

    provider = relationship("ServiceProvider", back_populates="lab_offerings")
    test = relationship("LabTest")