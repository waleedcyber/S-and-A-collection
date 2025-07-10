from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from uuid import uuid4
import os
from typing import Optional


import shutil
import os

router = APIRouter()

UPLOAD_DIR = "static/uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)  # Create upload folder if it doesn't exist

@router.post("/upload-image")
async def upload_image(image: UploadFile = File(...)):
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed.")

    file_path = os.path.join(UPLOAD_DIR, image.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    return {"filename": image.filename, "url": f"/static/uploads/{image.filename}"}


from database_setup import SessionLocal, engine
import models

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

# Serve uploaded images from /uploads
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/admin/upload")
def upload_product(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    quantity: int = Form(...),
    category_id: int = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Save image file
    file_ext = os.path.splitext(image.filename)[1]
    if file_ext.lower() not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise HTTPException(status_code=400, detail="Invalid image format")

    unique_filename = f"{uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    with open(file_path, "wb") as f:
        f.write(image.file.read())

    image_url = f"/uploads/{unique_filename}"

    # Save product to database
    product = models.Product(
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

@router.get("/products")
def get_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()
