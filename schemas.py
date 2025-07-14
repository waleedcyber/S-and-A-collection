# schemas.py

from pydantic import BaseModel
from typing import Optional
from typing import List

class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    quantity: int

    model_config = {
        "from_attributes": True
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