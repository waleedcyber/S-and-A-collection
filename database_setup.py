from sqlalchemy.orm import sessionmaker
from db import Base, engine
import models  # Ensure all tables are registered

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_tables()
    print("✅ Tables created successfully!")
