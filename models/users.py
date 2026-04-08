#models/users.py
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String,Boolean ,BigInteger, ForeignKey, Text, Numeric
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
    bookings = relationship("Booking", back_populates="user")
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    saved_address = Column(Text, nullable=True)

class Admin(Base):
    __tablename__ = "admins"
    admin_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default='admin')

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
    