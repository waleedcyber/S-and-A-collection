from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CategoryCreate(BaseModel):
    name: str

class CategoryOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}

class ProductCreate(BaseModel):
    name: str
    price: float
    category_ids: List[int]
    description: str
    quantity: int

class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    quantity: int
    image_url: Optional[str]
    categories: List[CategoryOut] = []
    model_config = {"from_attributes": True}

class OrderItem(BaseModel):
    name: str
    price: float
    quantity: int

class OrderCreate(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    items: List[OrderItem]
    total: float

class OrderOut(BaseModel):
    id: int
    order_id: str
    customer_name: str
    customer_phone: str
    customer_email: Optional[str]
    customer_address: Optional[str]
    item_names: str
    items: str
    total: float
    timestamp: datetime
    status: str
    payment_status: str
    payment_reference: Optional[str]
    paid_at: Optional[datetime]
    time_ago: Optional[str] = None
    model_config = {"from_attributes": True}

class ProductRequestSchema(BaseModel):
    product_id: int
    customer_name: str
    customer_email: str
    message: Optional[str]
    model_config = {"from_attributes": True}

class ProductRequestResponseSchema(BaseModel):
    id: int
    product_id: int
    customer_name: str
    customer_email: str
    message: str
    model_config = {"from_attributes": True}