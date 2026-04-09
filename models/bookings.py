import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Boolean, BigInteger, ForeignKey, Text, Numeric, DateTime, Integer
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    phone = Column(String)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    saved_address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow) # FIX: Added timestamp
    
    bookings = relationship("Booking", back_populates="user")

class Admin(Base):
    __tablename__ = "admins"
    admin_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default='admin')
    created_at = Column(DateTime, default=datetime.utcnow) # FIX: Added timestamp

class SavedAddress(Base):
    __tablename__ = "saved_addresses"
    address_id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    label = Column(String(50), nullable=False) # e.g., 'Home', 'Office'
    address_text = Column(Text, nullable=False)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    is_default = Column(Boolean, default=False) # 1 for True, 0 for False
    
    user = relationship("User", backref="saved_addresses")

class Booking(Base):
    __tablename__ = "bookings"
    booking_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.provider_id", ondelete="CASCADE"), nullable=False)
    
    # The Item Booked
    doctor_service_id = Column(BigInteger, ForeignKey("doctor_services.service_id", ondelete="SET NULL"))
    medicine_id = Column(BigInteger, ForeignKey("medicines.medicine_id", ondelete="SET NULL"))
    lab_test_id = Column(BigInteger, ForeignKey("lab_tests.test_id", ondelete="SET NULL"))
    
    # Booking Details
    scheduled_time = Column(DateTime)
    booking_status = Column(String(50), default='pending')
    delivery_address = Column(Text)
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    order_notes = Column(Text)
    
    # Patient Data (For the specific appointment)
    patient_name = Column(String(255))
    patient_age = Column(Integer)
    patient_gender = Column(String(50))
    symptoms = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="bookings")
    provider = relationship("ServiceProvider")
    doctor_service = relationship("DoctorService")
    medicine = relationship("Medicine") # FIX: Missing relationship added
    lab_test = relationship("LabTest")  # FIX: Missing relationship added

class MedicalRecord(Base):
    __tablename__ = "medical_records"
    record_id = Column(BigInteger, primary_key=True, autoincrement=True)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.booking_id", ondelete="SET NULL"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.provider_id", ondelete="CASCADE"), nullable=False)
    diagnosis = Column(Text)
    report_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    booking = relationship("Booking") # FIX: Added back-reference

class Review(Base):
    __tablename__ = "reviews"
    review_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.booking_id", ondelete="CASCADE"), unique=True, nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    booking = relationship("Booking") # FIX: Added back-reference

class Complaint(Base):
    __tablename__ = "complaints"
    complaint_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) 
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.booking_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.provider_id", ondelete="CASCADE"), nullable=False)
    complaint_text = Column(Text, nullable=False)
    status = Column(String(50), default='open')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    booking = relationship("Booking") 