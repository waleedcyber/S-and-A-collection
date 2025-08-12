from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base  # ✅ updated import for SQLAlchemy 2.0
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from config import DATABASE_URL
# Change this to your actual DB path if different

import os

load_dotenv() # Load environment variables from .env file
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()



      