from database_setup import SessionLocal
from models import Admin
from auth import get_password_hash

# --- Define your new credentials here ---
new_username = "waleed"
new_password = "wal33d"  # You can change this

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
