from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from utils.order_id_generator import generate_order_id
from database_setup import get_db
from models import Order, Product
from schemas import OrderCreate
import json
import os

router = APIRouter()

@router.get("/products")
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

@router.post("/orders")
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    order_id = generate_order_id()

    item_names = ", ".join([item.name for item in order.items])
    items_json = json.dumps([item.dict() for item in order.items])

    new_order = Order(
        order_id=order_id,
        customer_name=order.name,
        customer_email=order.email,
        customer_address=order.address or "",
        item_names=item_names,
        items=items_json,
        total=order.total,
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return {
        "message": "Order placed successfully ✅",
        "order_id": order_id
    }
