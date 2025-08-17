from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form, Query, Request
from sqlalchemy.orm import Session
from db import get_db
from models import Product, Category
from schemas import ProductCreate, ProductOut
import os
import random

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/products")
def create_product(
    name: str = Form(...),
    price: float = Form(...),
    description: str = Form(...),
    quantity: int = Form(...),
    category_id: int = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Save the image
    file_path = os.path.join(UPLOAD_DIR, image.filename)
    with open(file_path, "wb") as f:
        f.write(image.file.read())

    # Check if the category exists
    category_obj = db.query(Category).filter_by(id=category_id).first()
    if not category_obj:
        raise HTTPException(status_code=400, detail="Invalid category ID")

    # Save product with proper image URL path
    new_product = Product(
        name=name,
        price=price,
        description=description,
        quantity=quantity,
        category_id=category_id,
        image_url=f"/uploads/{image.filename}"
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return {
        "message": "Product created successfully",
        "product": {
            "id": new_product.id,
            "name": new_product.name,
            "price": new_product.price,
            "description": new_product.description,
            "quantity": new_product.quantity,
            "category_id": new_product.category_id,
            "image_url": new_product.image_url,
        }
    }

@router.get("/products", response_model=List[ProductOut])
def get_products(
    request: Request,
    db: Session = Depends(get_db),
    category_id: int = Query(None),
    sort_by: str = Query(None)
):
    query = db.query(Product)

    if category_id:
        query = query.filter(Product.category_id == category_id)

    if sort_by == "price":
        query = query.order_by(Product.price)
    elif sort_by == "name":
        query = query.order_by(Product.name)
    else:
        query = query.order_by(Product.id.desc())

    products = query.all()

    # Inject full image URL for each product
    for product in products:
        if product.image_url and not product.image_url.startswith("http"):
            filename = product.image_url.split("/")[-1]
            product.image_url = f"{request.base_url}uploads/{filename}"

    return products

@router.get("/products/random", response_model=List[ProductOut])
def get_random_products(db: Session = Depends(get_db)):
    all_products = db.query(Product).all()
    sample_size = min(6, len(all_products))
    random_products = random.sample(all_products, sample_size) if all_products else []
    return random_products

@router.get("/categories", tags=["Categories"])
def get_categories(db: Session = Depends(get_db)):
    """
    Public endpoint: fetch all categories (no admin required).
    """
    categories = db.query(Category).all()
    return [{"id": c.id, "name": c.name} for c in categories]
