from sqlalchemy import Column, Integer, String, Float, Text
from Core.database import Base

class Products(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    stock  = Column(Integer, nullable=True)