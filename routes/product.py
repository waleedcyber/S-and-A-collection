from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from utils.order_id_generator import generate_order_id
from database_setup import get_db
from models import Product, Order, Category
from schemas import ProductCreate, ProductOut, OrderCreate

import json
import os

router = APIRouter()

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
    # ✅ Make sure uploads folder exists
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    # ✅ Save the image
    file_path = os.path.join(upload_dir, image.filename)
    with open(file_path, "wb") as f:
        f.write(image.file.read())

    # ✅ Check if the category exists
    category_obj = db.query(Category).filter_by(id=category_id).first()
    if not category_obj:
        raise HTTPException(status_code=400, detail="Invalid category ID")

    # ✅ Save product with proper image URL path
    new_product = Product(
        name=name,
        price=price,
        description=description,
        quantity=quantity,
        category_id=category_id,
        image_url=f"/uploads/{image.filename}"  # 🔥 This makes it usable from frontend
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

@router.get("/products")
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()


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
