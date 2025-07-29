from db import SessionLocal
from models import Category

# Connect to the DB
db = SessionLocal()

# Create test categories
categories = [
    Category(id=1, name="Fashion"),
    Category(id=2, name="Electronics"),
    Category(id=3, name="Beauty")
]

# Add to DB
db.add_all(categories)
db.commit()
db.close()

print("Test categories added successfully ✅")
