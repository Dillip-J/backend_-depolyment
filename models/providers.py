# models/providers.py
import uuid
from sqlalchemy import Column, String, BigInteger, Boolean, Numeric, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base

class ServiceProvider(Base):
    __tablename__ = "service_providers"
    __table_args__ = {'extend_existing': True} 
    
    provider_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_type = Column(String(50), nullable=False) 
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True) 
    price = Column(Numeric(10, 2), nullable=True) 
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
    bio = Column(Text, nullable=True) 
    bank_name = Column(String(100), nullable=True)
    account_number = Column(String(50), nullable=True)
    ifsc_code = Column(String(20), nullable=True)

    # 🚨 FIX: Pass the exact class name as a string, no importing needed!
    doctor_services = relationship("DoctorService", back_populates="provider", cascade="all, delete")
    pharmacy_inventory = relationship("PharmacyInventory", back_populates="provider", cascade="all, delete")
    lab_offerings = relationship("LabOffering", back_populates="provider", cascade="all, delete")
    bookings = relationship("Booking", back_populates="provider", cascade="all, delete")
    availabilities = relationship("ProviderAvailability", back_populates="provider", cascade="all, delete")


class ProviderAvailability(Base):
    __tablename__ = "provider_availability"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.provider_id", ondelete="CASCADE"))
    day_of_week = Column(String) 
    time_slot = Column(String)  
    
    provider = relationship("ServiceProvider", back_populates="availabilities")


class DoctorService(Base):
    __tablename__ = "doctor_services"
    __table_args__ = {'extend_existing': True}
    
    service_id = Column(BigInteger, primary_key=True, autoincrement=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.provider_id", ondelete="CASCADE"), nullable=False)
    service_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False) 
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    image_url = Column(String(500), nullable=True)
    status = Column(String(50), default='active')

    provider = relationship("ServiceProvider", back_populates="doctor_services")


class Medicine(Base):
    __tablename__ = "medicines"
    __table_args__ = {'extend_existing': True}
    
    medicine_id = Column(BigInteger, primary_key=True, autoincrement=True)
    medicine_name = Column(String(255), nullable=False)
    manufacturer = Column(String(255))
    requires_prescription = Column(Boolean, default=False)
    description = Column(Text)
    image_url = Column(String(500), nullable=True)


class PharmacyInventory(Base):
    __tablename__ = "pharmacy_inventory"
    __table_args__ = {'extend_existing': True}
    
    inventory_id = Column(BigInteger, primary_key=True, autoincrement=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.provider_id", ondelete="CASCADE"), nullable=False)
    medicine_id = Column(BigInteger, ForeignKey("medicines.medicine_id", ondelete="CASCADE"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    in_stock = Column(Boolean, default=True)
    custom_description = Column(Text, nullable=True)
    custom_image_url = Column(String(500), nullable=True)

    provider = relationship("ServiceProvider", back_populates="pharmacy_inventory")
    medicine = relationship("Medicine")


class LabTest(Base):
    __tablename__ = "lab_tests"
    __table_args__ = {'extend_existing': True}
    
    test_id = Column(BigInteger, primary_key=True, autoincrement=True)
    test_name = Column(String(255), nullable=False)
    category = Column(String(100))
    description = Column(Text)


class LabOffering(Base): 
    __tablename__ = "lab_test_offerings"
    __table_args__ = {'extend_existing': True}
    
    offering_id = Column(BigInteger, primary_key=True, autoincrement=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.provider_id", ondelete="CASCADE"), nullable=False)
    test_id = Column(BigInteger, ForeignKey("lab_tests.test_id", ondelete="CASCADE"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    home_collection_available = Column(Boolean, default=False)
    preparation_rules = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)

    provider = relationship("ServiceProvider", back_populates="lab_offerings")
    lab_test = relationship("LabTest")
# 🚨 NOTICE: CATALOG ITEM IS GONE FROM THIS FILE. IT LIVES IN CATALOG.PY NOW.

# # models/providers.py
# import uuid
# from sqlalchemy import Column, String, Numeric, Text, ForeignKey, Integer
# from sqlalchemy.dialects.postgresql import UUID
# from sqlalchemy.orm import relationship
# from database import Base

# class ServiceProvider(Base):
#     __tablename__ = "service_providers"
#     __table_args__ = {'extend_existing': True} 
    
#     provider_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     provider_type = Column(String(50), nullable=False, default='Doctor') 
#     name = Column(String(255), nullable=False)
#     category = Column(String(100), nullable=True) 
#     consultation_fee = Column(Numeric(10, 2), default=500.00) 
#     email = Column(String(255), unique=True, index=True, nullable=False)
#     password = Column(String(255), nullable=False)
#     phone = Column(String(20))
#     address = Column(Text)
#     latitude = Column(Numeric(10, 8))
#     longitude = Column(Numeric(11, 8))
#     status = Column(String(50), default='pending')
#     profile_photo_url = Column(String(500))
#     bio = Column(Text, nullable=True) 
#     bank_name = Column(String(100), nullable=True)
#     account_number = Column(String(50), nullable=True)
#     ifsc_code = Column(String(20), nullable=True)

#     bookings = relationship("Booking", back_populates="provider", cascade="all, delete")
#     availabilities = relationship("ProviderAvailability", back_populates="provider", cascade="all, delete")


# class ProviderAvailability(Base):
#     __tablename__ = "provider_availability"
#     __table_args__ = {'extend_existing': True}
    
#     id = Column(Integer, primary_key=True, index=True)
#     provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.provider_id", ondelete="CASCADE"))
#     day_of_week = Column(String) 
#     time_slot = Column(String)  
    
#     provider = relationship("ServiceProvider", back_populates="availabilities")