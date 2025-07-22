# schemas.py

from pydantic import BaseModel
from typing import Optional
from typing import List
from pydantic import BaseModel
from typing import Optional


class ProductCreate(BaseModel):
    name: str
    price: float
    category_id: int  # ✅ Changed from 'category' to 'category_id'
    description: str
    quantity: int

class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    quantity: int
    image_url: Optional[str]
    category_id: int

    model_config = {
        "from_attributes": True  # ✅ Pydantic v2 way
    }
        

class OrderItem(BaseModel):
    name: str
    price: float
    quantity: int

class OrderCreate(BaseModel):
    name: str
    email: str
    items: List[OrderItem]
    total: float