# main.py
from fastapi import FastAPI,Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# Local imports
from database_setup import create_tables
from routes.product import router as product_router
from routes.admin import router as admin_router
from routes.product_request import router as product_request_router

 
from sqlalchemy.orm import Session
from db import SessionLocal
from models import Category
# ✅ Lifespan setup (runs once at startup)
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield

# ✅ Create FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",  # local testing
        "http://localhost:5500",  # local alternative
        "https://sandscollection.onrender.com",  # if you host frontend on same backend
        "https://s-and-s-collection.onrender.com",  # replace with your deployed frontend domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
app.get("/categories", tags=["Categories"])
def get_categories(db: Session = Depends(get_db)):
    """
    Public endpoint: fetch all categories (no admin required).
    """
    categories = db.query(Category).all()
    return [{"id": c.id, "name": c.name} for c in categories]


# ✅ Include routers under /api
app.include_router(product_router, prefix="/api", tags=["Products"])
app.include_router(admin_router, prefix="/api", tags=["Admin"])
app.include_router(product_request_router, prefix="/api", tags=["Product Requests"])

# ✅ Static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/", StaticFiles(directory=".", html=True), name="root")
