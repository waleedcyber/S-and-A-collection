# schemas.py

from pydantic import BaseModel
from typing import Optional

class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    quantity: int

    class Config:
        orm_mode = True
