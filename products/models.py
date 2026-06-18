from sqlalchemy import Column, Integer, ForeignKey, Enum, Float, String, DateTime, BigInteger
from CRUD.models import Products
from sqlalchemy.orm import relationship
from Core.database import Base
import enum
from datetime import datetime

class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    product_id = Column(BigInteger, ForeignKey("products.id"), nullable=False)
    amount = Column(Integer, nullable=False, default=1) 
    cart = relationship("Cart", back_populates="items")
    product = relationship("Products") 

class StatusEnum(str, enum.Enum):
    PENDING = "pendiente"
    PAID = "pagado"
    FAILED = "fallido"

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    total = Column(Float, nullable=False, default=0.0)
    stripe_payment_id = Column(String(255), unique=True, nullable=True)
    status = Column(Enum(StatusEnum), default=StatusEnum.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    details = relationship("DetalleOrden", back_populates="order", cascade="all, delete-orphan")


class DetalleOrden(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(BigInteger, ForeignKey("products.id"), nullable=False)
    amount = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="details")
    product = relationship("Products")

