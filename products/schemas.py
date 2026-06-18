from pydantic import BaseModel
from typing import List
from datetime import datetime

class CartItemCreate(BaseModel):
    product_id: int
    amount: int

class ProductSchema(BaseModel):
    id: int
    name: str
    price: float

class CartItemResponse(BaseModel):
    id: int
    cart_id: int
    amount: int
    product: ProductSchema

class ProductoBase(BaseModel):
    name: str
    price: float

class ProductoResponse(ProductoBase):
    id: int
    class Config:
        from_attributes = True

class DetalleOrdenBase(BaseModel):
    product_id: int
    amount: int

class DetalleOrdenResponse(BaseModel):
    id: int
    product_id: int
    amount: int
    unit_price: float
    product: ProductoResponse

    class Config:
        from_attributes = True

class CrearOrden(BaseModel):
    user_id: int
    items: List[DetalleOrdenBase]

class OrdenResponse(BaseModel):
    id: int
    user_id: int
    total: float
    status: str
    created_at: datetime
    details: List[DetalleOrdenResponse]

    class Config:
        from_attributes = True