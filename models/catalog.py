#models/catalog.py
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, BigInteger, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship
from database import Base

class Service(Base):
    __tablename__ = "services"
    service_id = Column(BigInteger, primary_key=True, index=True)
    service_name = Column(String, nullable=False)
    category = Column(String)
    base_price = Column(Numeric(10, 2))

class CatalogItem(Base):
    __tablename__ = "catalog_items"
    # A global list of everything that can be bought
    item_id = Column(BigInteger, primary_key=True, index=True)
    item_name = Column(String, nullable=False) # e.g., "Paracetamol 500mg" or "Thyroid Panel"
    item_type = Column(String, nullable=False) # 'Medicine' or 'LabTest'
    category = Column(String) # e.g., 'Painkillers', 'Blood Work'
    description = Column(Text)
