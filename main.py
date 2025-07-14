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

# ✅ Create FastAPI app
app = FastAPI()

# ✅ CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Serve static/uploads
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ✅ DB startup
@app.on_event("startup")
def startup():
    create_tables()

# ✅ Reusable DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Auth JWT dependency
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

# ✅ Root route
@app.get("/")
def read_root():
    return {"message": "Welcome to your shopping site 🛍️"}

# ✅ Admin login
@app.post("/admin/login")
def login_admin(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == form_data.username).first()
    if not admin or not auth.verify_password(form_data.password, admin.password):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    access_token = auth.create_access_token(data={"sub": admin.username})
    return {"access_token": access_token, "token_type": "bearer"}

# ✅ Admin-only route for product requests
@app.get("/admin/product-requests")
def get_product_requests(db: Session = Depends(get_db), current_admin: str = Depends(get_current_admin)):
    return db.query(ProductRequest).all()

# ✅ Route to request product (user side)
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

# ✅ Optional legacy route (still OK to keep if you're using Form-based order)
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

# ✅ Product list for old route (still OK)
@app.get("/products", response_model=List[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

# ✅ Import and include routers
from routes.product import router as product_router
from routes.admin import router as admin_router
app.include_router(product_router)
app.include_router(admin_router)
