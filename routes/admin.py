from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models import Product
from models import Order
from models import Category
from schemas import ProductRequestResponseSchema
from schemas import CategoryCreate
from models import ProductRequest
import auth
from auth import get_current_admin  # Protect admin routes
from uuid import uuid4
import os
import shutil
from datetime import datetime
from typing import List 


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

@router.delete("/admin/products/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Optional: Delete the image file from the server
    if product.image_url:
        file_path = product.image_url.lstrip("/") # remove leading slash
        if os.path.exists(file_path):
            os.remove(file_path)

    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}

@router.post("/admin/categories", status_code=201)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    # Check if category already exists
    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    new_category = Category(name=category.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return {"message": "Category created", "category": {"id": new_category.id, "name": new_category.name}}

@router.get("/admin/categories")
def list_categories(
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    categories = db.query(Category).all()
    return [{"id": c.id, "name": c.name} for c in categories]

@router.put("/admin/categories/{category_id}")
def update_category(
    category_id: int, 
    category: CategoryCreate, 
    db: Session = Depends(get_db), 
    admin: dict = Depends(get_current_admin)
):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    cat.name = category.name
    db.commit()
    db.refresh(cat)
    return {"id": cat.id, "name": cat.name}

@router.delete("/admin/categories/{category_id}")
def delete_category(
    category_id: int, 
    db: Session = Depends(get_db), 
    admin: dict = Depends(get_current_admin)
):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(cat)
    db.commit()
    return {"detail": "Category deleted"}