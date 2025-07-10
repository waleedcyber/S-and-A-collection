from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from db import Base, engine
import models  # makes sure all tables are seen

def create_tables():
    Base.metadata.create_all(bind=engine)

import models  # This makes sure SQLAlchemy sees all table classes


Base = declarative_base()


# Create the SQLite engine
DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)
if __name__ == "__main__":
    create_tables()
    print("✅ Tables created successfully!")
# This script sets up the database connection and creates the necessary tables.