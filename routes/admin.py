from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from database_setup import get_db
from models import Product
from uuid import uuid4
import os
import shutil

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
