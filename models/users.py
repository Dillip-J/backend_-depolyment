# models/users.py
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Boolean, BigInteger, ForeignKey, Text, Numeric, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    phone = Column(String)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    saved_address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 🚨 FIX: Pass the exact class name as a string, no importing needed!
    saved_addresses = relationship("SavedAddress", back_populates="user", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")


class Admin(Base):
    __tablename__ = "admins"
    __table_args__ = {'extend_existing': True}
    
    admin_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default='admin')
    created_at = Column(DateTime, default=datetime.utcnow)


class SavedAddress(Base):
    __tablename__ = "saved_addresses"
    __table_args__ = {'extend_existing': True}
    
    address_id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    label = Column(String(50), nullable=False)
    address_text = Column(Text, nullable=False)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    is_default = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="saved_addresses")