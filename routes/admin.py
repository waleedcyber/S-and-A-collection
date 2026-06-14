from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from fastapi.security import OAuth2PasswordRequestForm
from models import Product, Order, Category, ProductRequest
from schemas import ProductRequestResponseSchema, CategoryCreate
from models import Admin
from auth import get_current_admin
from auth import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import datetime, timedelta
from typing import List, Optional
import cloudinary
import cloudinary.uploader
import os

router = APIRouter()

# Cloudinary config
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)


@router.post("/admin/login")
def admin_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == form_data.username).first()
    if not admin:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    if not verify_password(form_data.password, admin.password):
        raise HTTPException(status_code=400, detail="Invalid username or password")

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
    category_ids: str = Form(...),  # comma-separated e.g. "1,2,3"
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    # Validate image format
    file_ext = os.path.splitext(image.filename)[1].lower()
    if file_ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise HTTPException(status_code=400, detail="Invalid image format")

    # Parse category IDs
    try:
        ids = [int(i.strip()) for i in category_ids.split(",") if i.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid category IDs")

    if not ids:
        raise HTTPException(status_code=400, detail="Please select at least one category")

    # Fetch category objects
    categories = db.query(Category).filter(Category.id.in_(ids)).all()
    if not categories:
        raise HTTPException(status_code=400, detail="No valid categories found")

    # Upload to Cloudinary
    try:
        result = cloudinary.uploader.upload(
            image.file,
            folder="s_and_s_collection",
            resource_type="image",
        )
        image_url = result["secure_url"]
        public_id = result["public_id"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

    # Create product with many-to-many categories
    product = Product(
        name=name,
        description=description,
        price=price,
        quantity=quantity,
        image_url=image_url,
        cloudinary_public_id=public_id,
        categories=categories,  # ✅ assign list of category objects
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    return {
        "message": "Product uploaded successfully",
        "product": {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "quantity": product.quantity,
            "image_url": product.image_url,
            "categories": [{"id": c.id, "name": c.name} for c in product.categories],
        }
    }


@router.get("/admin/products", tags=["Admin"])
def get_all_products(db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)):
    products = db.query(Product).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "quantity": p.quantity,
            "description": p.description,
            "image_url": p.image_url,
            "categories": [{"id": c.id, "name": c.name} for c in p.categories],
        }
        for p in products
    ]


@router.delete("/admin/products/{product_id}", status_code=204, tags=["Admin"])
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.cloudinary_public_id:
        try:
            cloudinary.uploader.destroy(product.cloudinary_public_id)
        except Exception:
            pass

    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}


@router.get("/admin/products/{product_id}", tags=["Admin"])
def get_product(product_id: int, db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "quantity": product.quantity,
        "description": product.description,
        "image_url": product.image_url,
        "categories": [{"id": c.id, "name": c.name} for c in product.categories],
    }


@router.put("/admin/products/{product_id}", tags=["Admin"])
def update_product(
    product_id: int,
    name: str = Form(...),
    description: str = Form(None),
    price: float = Form(...),
    quantity: int = Form(...),
    category_ids: str = Form(...),  # comma-separated
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.name = name
    product.description = description
    product.price = price
    product.quantity = quantity

    # Update categories
    try:
        ids = [int(i.strip()) for i in category_ids.split(",") if i.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid category IDs")

    categories = db.query(Category).filter(Category.id.in_(ids)).all()
    product.categories = categories  # ✅ replaces old categories

    if image is not None:
        file_ext = os.path.splitext(image.filename)[1].lower()
        if file_ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            raise HTTPException(status_code=400, detail="Invalid image format")

        if product.cloudinary_public_id:
            try:
                cloudinary.uploader.destroy(product.cloudinary_public_id)
            except Exception:
                pass

        try:
            result = cloudinary.uploader.upload(
                image.file,
                folder="s_and_s_collection",
                resource_type="image",
            )
            product.image_url = result["secure_url"]
            product.cloudinary_public_id = result["public_id"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

    db.commit()
    db.refresh(product)
    return {
        "message": "Product updated",
        "product": {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "quantity": product.quantity,
            "image_url": product.image_url,
            "categories": [{"id": c.id, "name": c.name} for c in product.categories],
        }
    }


@router.post("/admin/categories", status_code=201, tags=["Admin Categories"])
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    new_category = Category(name=category.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return {"message": "Category created", "category": {"id": new_category.id, "name": new_category.name}}


@router.get("/admin/categories", tags=["Admin Categories"])
def list_categories(db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)):
    categories = db.query(Category).all()
    return [{"id": c.id, "name": c.name} for c in categories]


@router.put("/admin/categories/{category_id}", tags=["Admin Categories"])
def update_category(
    category_id: int,
    category: CategoryCreate,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    cat.name = category.name
    db.commit()
    db.refresh(cat)
    return {"id": cat.id, "name": cat.name}


@router.delete("/admin/categories/{category_id}", tags=["Admin Categories"])
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(cat)
    db.commit()
    return {"detail": "Category deleted"}


@router.get("/products/random", tags=["Products"])
def get_random_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "quantity": p.quantity,
            "description": p.description,
            "image_url": p.image_url,
            "categories": [{"id": c.id, "name": c.name} for c in p.categories],
        }
        for p in products
    ]


@router.get("/product-requests", response_model=List[ProductRequestResponseSchema], tags=["Admin"])
def get_all_product_requests(db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)):
    return db.query(ProductRequest).all()


@router.put("/orders/{order_id}/mark_paid", tags=["Admin"])
def mark_order_paid(
    order_id: int, db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)
):
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
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = "Delivered"
    db.commit()
    return {"message": "Marked as delivered"}