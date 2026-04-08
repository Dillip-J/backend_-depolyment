# models/booking.py
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, BigInteger, Boolean, Numeric, Text, ForeignKey, DateTime, Integer
from sqlalchemy.orm import relationship
from database import Base
import uuid
from datetime import datetime

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


class MedicalRecord(Base):
    __tablename__ = "medical_records"
    record_id = Column(BigInteger, primary_key=True, autoincrement=True)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.booking_id", ondelete="SET NULL"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.provider_id", ondelete="CASCADE"), nullable=False)
    diagnosis = Column(Text)
    report_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

class Review(Base):
    __tablename__ = "reviews"
    review_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) # Updated to UUID based on SQL
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.booking_id", ondelete="CASCADE"), unique=True, nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Complaint(Base):
    __tablename__ = "complaints"
    complaint_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) # Updated to UUID based on SQL
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.booking_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.provider_id", ondelete="CASCADE"), nullable=False)
    complaint_text = Column(Text, nullable=False)
    status = Column(String(50), default='open')
    created_at = Column(DateTime, default=datetime.utcnow)

class ServiceReport(Base):
    __tablename__ = "service_report"
    report_id = Column(BigInteger, primary_key=True, autoincrement=True)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.booking_id", ondelete="CASCADE"), unique=True, nullable=False)
    rating = Column(Integer)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)