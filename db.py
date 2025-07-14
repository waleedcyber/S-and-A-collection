from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base  # ✅ updated import for SQLAlchemy 2.0
from sqlalchemy.orm import sessionmaker

# Change this to your actual DB path if different
DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
