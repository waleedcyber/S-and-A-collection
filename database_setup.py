from sqlalchemy import create_engine
from models import Admin
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.declarative import declarative_base
from db import Base, engine
import models  # makes sure all tables are seen

def create_tables():
    Base.metadata.create_all(bind=engine)

import models  # This makes sure SQLAlchemy sees all table classes



# Create a session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)
if __name__ == "__main__":
    create_tables()
    print("✅ Tables created successfully!")
# This script sets up the database connection and creates the necessary tables.

from database_setup import create_tables

create_tables()
print("✅ Tables created")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
