# models/bookings.py
import secrets
import string
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, BigInteger, Numeric, Text, ForeignKey, DateTime, Integer
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

def generate_booking_string():
    chars = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    return f"BKG-{chars}"

class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = {'extend_existing': True} 
    
    # 🚨 FIXED: Changed to 40 so your old UUIDs don't crash the database!
    booking_id = Column(String(40), primary_key=True, default=generate_booking_string, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.provider_id", ondelete="CASCADE"), nullable=False)
    
    doctor_service_id = Column(BigInteger, ForeignKey("doctor_services.service_id", ondelete="SET NULL"))
    medicine_id = Column(BigInteger, ForeignKey("medicines.medicine_id", ondelete="SET NULL"))
    lab_test_id = Column(BigInteger, ForeignKey("lab_tests.test_id", ondelete="SET NULL"))
    
    scheduled_time = Column(DateTime)
    booking_status = Column(String(50), default='pending')
    delivery_address = Column(Text)
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    order_notes = Column(Text)
    
    patient_name = Column(String(255))
    patient_age = Column(Integer)
    patient_gender = Column(String(50))
    symptoms = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="bookings")
    provider = relationship("ServiceProvider", back_populates="bookings")
    doctor_service = relationship("DoctorService")
    medicine = relationship("Medicine") 
    lab_test = relationship("LabTest")  


class MedicalRecord(Base):
    __tablename__ = "medical_records"
    __table_args__ = {'extend_existing': True}
    
    record_id = Column(BigInteger, primary_key=True, autoincrement=True)
    # 🚨 FIXED: Changed to 40
    booking_id = Column(String(40), ForeignKey("bookings.booking_id", ondelete="SET NULL"))
    diagnosis = Column(Text)
    report_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    booking = relationship("Booking")


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = {'extend_existing': True}
    
    review_id = Column(Integer, primary_key=True, autoincrement=True)
    # 🚨 FIXED: Changed to 40
    booking_id = Column(String(40), ForeignKey("bookings.booking_id", ondelete="CASCADE"), unique=True, nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    booking = relationship("Booking") 


class Complaint(Base):
    __tablename__ = "complaints"
    __table_args__ = {'extend_existing': True}
    
    complaint_id = Column(Integer, primary_key=True, autoincrement=True) 
    # 🚨 FIXED: Changed to 40
    booking_id = Column(String(40), ForeignKey("bookings.booking_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.provider_id", ondelete="CASCADE"), nullable=False)
    complaint_text = Column(Text, nullable=False)
    status = Column(String(50), default='open')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    booking = relationship("Booking")


class VideoMeeting(Base):
    __tablename__ = "video_meetings"
    __table_args__ = {'extend_existing': True}

    meeting_id = Column(BigInteger, primary_key=True, autoincrement=True)
    # 🚨 FIXED: Changed to 40
    booking_id = Column(String(40), ForeignKey("bookings.booking_id", ondelete="CASCADE"), unique=True, nullable=False)
    room_name = Column(String(255), unique=True, nullable=False)
    host_url = Column(Text, nullable=False)
    join_url = Column(Text, nullable=False)
    status = Column(String(50), default="waiting")
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)

    booking = relationship("Booking", backref="video_meeting")

# # models/bookings.py
# import secrets
# import string
# from sqlalchemy.dialects.postgresql import UUID
# from sqlalchemy import Column, String, BigInteger, Numeric, Text, ForeignKey, DateTime, Integer
# from sqlalchemy.orm import relationship
# from database import Base
# from datetime import datetime

# def generate_booking_string():
#     chars = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
#     return f"BKG-{chars}"

# class Booking(Base):
#     __tablename__ = "bookings"
#     __table_args__ = {'extend_existing': True} 
    
#     booking_id = Column(String(40), primary_key=True, default=generate_booking_string, index=True)
#     user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
#     provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.provider_id", ondelete="CASCADE"), nullable=False)
    
#     scheduled_time = Column(DateTime)
#     booking_status = Column(String(50), default='pending')
    
#     delivery_address = Column(Text)
#     latitude = Column(Numeric(10, 8))
#     longitude = Column(Numeric(11, 8))
#     total_amount = Column(Numeric(10, 2))
    
#     patient_name = Column(String(255))
#     patient_age = Column(Integer)
#     patient_gender = Column(String(50))
    
#     symptoms = Column(Text)
#     clinical_notes = Column(Text)
    
#     created_at = Column(DateTime, default=datetime.utcnow)

#     # Relationships
#     user = relationship("User", back_populates="bookings")
#     provider = relationship("ServiceProvider", back_populates="bookings")


# class VideoMeeting(Base):
#     __tablename__ = "video_meetings"
#     __table_args__ = {'extend_existing': True}

#     meeting_id = Column(BigInteger, primary_key=True, autoincrement=True)
#     booking_id = Column(String(40), ForeignKey("bookings.booking_id", ondelete="CASCADE"), unique=True, nullable=False)
#     room_name = Column(String(255), unique=True, nullable=False)
#     host_url = Column(Text, nullable=False)
#     join_url = Column(Text, nullable=False)
#     status = Column(String(50), default="waiting")
#     created_at = Column(DateTime, default=datetime.utcnow)

#     booking = relationship("Booking", backref="video_meeting")