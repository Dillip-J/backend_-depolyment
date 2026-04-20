# models/catalog.py
from sqlalchemy import Column, String, BigInteger, Text, Numeric
from database import Base

class Service(Base):
    __tablename__ = "services"
    __table_args__ = {'extend_existing': True}
    
    service_id = Column(BigInteger, primary_key=True, index=True)
    service_name = Column(String, nullable=False)
    category = Column(String)
    base_price = Column(Numeric(10, 2))

class CatalogItem(Base):
    __tablename__ = "catalog_items"
    __table_args__ = {'extend_existing': True}
    
    item_id = Column(BigInteger, primary_key=True, index=True)
    item_name = Column(String, nullable=False) 
    item_type = Column(String, nullable=False) 
    category = Column(String) 
    description = Column(Text)