from database_setup import SessionLocal, create_tables  # ✅ Import create_tables
from models import Admin
from auth import get_password_hash

# --- ✅ Create tables before using them ---
create_tables()

# --- Define your new credentials here ---
new_username = "waleed"
new_password = "wal33d"

# --- Step 1: Connect to DB
db = SessionLocal()

try:
    # --- Step 2: Delete all old admins
    db.query(Admin).delete()
    db.commit()

    # --- Step 3: Hash new password
    hashed_password = get_password_hash(new_password)

    # --- Step 4: Create and add new admin
    new_admin = Admin(username=new_username, password=hashed_password)
    db.add(new_admin)
    db.commit()

    print("✅ Admin credentials reset successfully!")
    print(f"🔐 New Username: {new_username}")
    print(f"🔐 New Password: {new_password}")
finally:
    db.close()
