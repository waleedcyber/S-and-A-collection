from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from fastapi.security import OAuth2PasswordRequestForm
from models import Product, Order, Category, ProductRequest
from schemas import ProductRequestResponseSchema, CategoryCreate
from models import Admin
from auth import get_current_admin
from auth import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from uuid import uuid4
import os
from datetime import datetime
from typing import List
import shutil

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/admin/login")
def admin_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. Find admin in DB
    admin = db.query(Admin).filter(Admin.username == form_data.username).first()
    if not admin:
        raise HTTPException(status_code=400, detail="Invalid username or password")

    # 2. Verify password
    if not verify_password(form_data.password, admin.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    # 3. Create JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": admin.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/admin/upload", tags=["Admin"])
def upload_product(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    quantity: int = Form(...),
    category_id: int = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """
    Upload a new product.

    This endpoint is protected and can only be accessed by an admin.
    """
    file_ext = os.path.splitext(image.filename)[1]
    if file_ext.lower() not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise HTTPException(status_code=400, detail="Invalid image format")

    unique_filename = f"{uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    image_url = f"/uploads/{unique_filename}"

    product = Product(
        name=name,
        description=description,
        price=price,
        quantity=quantity,
        category_id=category_id,
        image_url=image_url,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    return {"message": "Product uploaded successfully", "product": product}


@router.get("/admin/products", tags=["Admin"])
def get_all_products(
    db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)
):
    """
    Get all products.

    This endpoint is protected and can only be accessed by an admin.
    """
    products = db.query(Product).all()
    return products


@router.delete("/admin/products/{product_id}", status_code=204, tags=["Admin"])
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """
    Delete a product by its ID.

    This endpoint is protected and can only be accessed by an admin.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Delete the image file from the server
    if product.image_url:
        file_path = product.image_url.lstrip("/")  # Remove leading slash
        if os.path.exists(file_path):
            os.remove(file_path)

    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}


@router.post("/admin/categories", status_code=201, tags=["Admin"])
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """
    Create a new category.

    This endpoint is protected and can only be accessed by an admin.
    """
    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    new_category = Category(name=category.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return {
        "message": "Category created",
        "category": {"id": new_category.id, "name": new_category.name},
    }


@router.get("/admin/categories", tags=["Admin"])
def list_categories(
    db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)
):
    """
    Get all categories.

    This endpoint is protected and can only be accessed by an admin.
    """
    categories = db.query(Category).all()
    return [{"id": c.id, "name": c.name} for c in categories]


@router.put("/admin/categories/{category_id}", tags=["Admin"])
def update_category(
    category_id: int,
    category: CategoryCreate,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """
    Update a category by its ID.

    This endpoint is protected and can only be accessed by an admin.
    """
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    cat.name = category.name
    db.commit()
    db.refresh(cat)
    return {"id": cat.id, "name": cat.name}


@router.delete("/admin/categories/{category_id}", tags=["Admin"])
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """
    Delete a category by its ID.

    This endpoint is protected and can only be accessed by an admin.
    """
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(cat)
    db.commit()
    return {"detail": "Category deleted"}


@router.get("/products/random", tags=["Products"])
def get_random_products(db: Session = Depends(get_db)):
    """
    Get a list of all products.
    """
    products = db.query(Product).all()
    return products


@router.get(
    "/product-requests",
    response_model=List[ProductRequestResponseSchema],
    tags=["Admin"],
)
def get_all_product_requests(
    db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)
):
    """
    Get all product requests.

    This endpoint is protected and can only be accessed by an admin.
    """
    requests = db.query(ProductRequest).all()
    return requests


@router.put("/orders/{order_id}/mark_paid", tags=["Admin"])
def mark_order_paid(
    order_id: int, db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)
):
    """
    Mark an order as paid.

    This endpoint is protected and can only be accessed by an admin.
    """
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.payment_status = "Paid"
    order.paid = True
    order.paid_at = datetime.utcnow()
    db.commit()
    return {"message": "Marked as paid"}


@router.put("/orders/{order_id}/mark_delivered", tags=["Admin"])
def mark_order_delivered(
    order_id: int, db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)
):
    """
    Mark an order as delivered.

    This endpoint is protected and can only be accessed by an admin.
    """
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = "Delivered"
    db.commit()
    return {"message": "Marked as delivered"}