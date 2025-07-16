from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from db import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    image_url = Column(String)
    quantity = Column(Integer, default=0)

    
    
class ProductRequest(Base):
    __tablename__ = "product_requests"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    customer_name = Column(String)
    customer_contact = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product")



class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True, nullable=False)
    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=False)
    customer_address = Column(String, nullable=True)

    item_names = Column(Text, nullable=False)  # e.g., "Soap, Shampoo"
    items = Column(Text, nullable=False)       # JSON string of products

    total = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")

    payment_status = Column(String, default="pending")  # or use Boolean
    payment_reference = Column(String, nullable=True)   # Paystack/Flutterwave ref
    paid_at = Column(DateTime, nullable=True)


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)  # hash this in your login logic
