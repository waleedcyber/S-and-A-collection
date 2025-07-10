from fastapi import FastAPI, Depends, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import List

# --- Local imports ---
from database_setup import SessionLocal, create_tables
from models import Admin, Product, ProductRequest, Order
from schemas import ProductOut
import auth

from routes.product import router as product_router

app = FastAPI()
app.include_router(product_router)

# 🔥 Create app first
app = FastAPI()

# 🔗 Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📦 Mount uploads or static files (e.g., for image serving)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")  # Add this if handling image uploads

# 🔄 DB startup
@app.on_event("startup")
def startup():
    create_tables()

# --- Reusable DB session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Auth JWT dependency ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/login")

def get_current_admin(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception

# --- Routes ---
@app.get("/")
def read_root():
    return {"message": "Welcome to your shopping site 🛍️"}

@app.post("/admin/login")
def login_admin(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == form_data.username).first()
    if not admin or not auth.verify_password(form_data.password, admin.password):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    access_token = auth.create_access_token(data={"sub": admin.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/admin/add-product")
def add_product(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    quantity: int = Form(...),
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    product = Product(name=name, description=description, price=price, quantity=quantity)
    db.add(product)
    db.commit()
    db.refresh(product)
    return {
        "message": "Product added",
        "product": {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "quantity": product.quantity 
        }
    }

@app.get("/admin/product-requests")
def get_product_requests(db: Session = Depends(get_db), current_admin: str = Depends(get_current_admin)):
    return db.query(ProductRequest).all()

@app.post("/request-product")
def request_product(
    product_id: int = Form(...),
    customer_name: str = Form(...),
    customer_contact: str = Form(...),
    db: Session = Depends(get_db)
):
    request = ProductRequest(
        product_id=product_id,
        customer_name=customer_name,
        customer_contact=customer_contact
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return {"message": "Request submitted", "request_id": request.id}

@app.get("/products", response_model=List[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

@app.post("/order")
def place_order(
    product_id: int = Form(...),
    customer_name: str = Form(...),
    address: str = Form(...),
    quantity: int = Form(...),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"error": "Product not found"}
    order = Order(
        product_id=product_id,
        customer_name=customer_name,
        address=address,
        quantity=quantity
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return {
        "message": "Order placed",
        "order": {
            "id": order.id,
            "product": product.name,
            "customer_name": order.customer_name,
            "address": order.address,
            "quantity": order.quantity
        }
    }

# ✅ Finally: Import and include custom routers (after app is created)
from routes.product import router as product_router
app.include_router(product_router)
