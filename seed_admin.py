# seed_admin.py
from database import SessionLocal
from models.users import Admin
from passlib.context import CryptContext

# Set up the hashing engine exactly like your auth router uses
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed_super_admin():
    db = SessionLocal()
    try:
        # 1. Generate the secure hash for 'password123'
        hashed_password = pwd_context.hash("password123")
        
        # 2. Look for the admin we created via SQL earlier
        admin = db.query(Admin).filter(Admin.email == "admin@vision.com").first()
        
        if admin:
            # If found, update the plain text to the secure hash
            admin.password = hashed_password
            db.commit()
            print("✅ Success: Admin password updated to a secure hash!")
        else:
            # If not found, create them from scratch
            new_admin = Admin(
                name="Super Admin", 
                email="admin@vision.com", 
                password=hashed_password, 
                role="admin"
            )
            db.add(new_admin)
            db.commit()
            print("✅ Success: New Admin created with a secure hash!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_super_admin()