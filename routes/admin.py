from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models import Product
from models import Order
from uuid import uuid4
import os
import shutil
from datetime import datetime
from typing import List 
from schemas import ProductRequestResponseSchema
from models import ProductRequest
from auth import get_current_admin  # Protect admin routes


router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/admin/upload")
def upload_product(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    quantity: int = Form(...),
    category_id: int = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)  # Protect the route
):
    file_ext = os.path.splitext(image.filename)[1]
    if file_ext.lower() not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise HTTPException(status_code=400, detail="Invalid image format")

    unique_filename = f"{uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as f:
        f.write(image.file.read())

    image_url = f"/uploads/{unique_filename}"

    product = Product(
        name=name,
        description=description,
        price=price,
        quantity=quantity,
        category_id=category_id,
        image_url=image_url
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    return {"message": "Product uploaded successfully", "product": product}

@router.get("/admin/products")
def get_all_products(db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)):
    products = db.query(Product).all()

    return [
        {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "quantity": product.quantity,
            "description": product.description,
            "image_url": product.image_url
        }
        for product in products
    ]

# admin marking delivery as completed
@router.put("/orders/{order_id}/mark_paid")
def mark_order_paid(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.payment_status = "Paid"
    order.paid = True
    order.paid_at = datetime.utcnow()
    db.commit()
    return {"message": "Marked as paid"}

@router.put("/orders/{order_id}/mark_delivered")
def mark_order_delivered(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = "Delivered"
    db.commit()
    return {"message": "Marked as delivered"}


@router.get("/product-requests", response_model=list[ProductRequestResponseSchema])
def get_all_product_requests(db: Session = Depends(get_db)):
    requests = db.query(ProductRequest).all()
    return requests