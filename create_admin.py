# create_admin.py
from database import SessionLocal
import models
from utils.security import hash_password
import getpass

def create_master_admin():
    db = SessionLocal()
    try:
        print("\n=== 🛡️  MASTER ADMIN SETUP 🛡️  ===")
        name = input("Enter Admin Name: ")
        email = input("Enter Admin Email: ")
        
        # getpass hides the password as you type it (like a real terminal)
        raw_password = getpass.getpass("Enter Admin Password (typing will be hidden): ")

        # 1. Check if they already exist
        existing = db.query(models.Admin).filter(models.Admin.email == email).first()
        if existing:
            print(f"\n❌ Error: An admin with the email '{email}' already exists.")
            return

        # 2. Hash the password securely
        hashed_pwd = hash_password(raw_password)

        # 3. Save to database
        new_admin = models.Admin(
            name=name,
            email=email,
            password=hashed_pwd,
            role="super_admin" 
        )

        db.add(new_admin)
        db.commit()
        
        print(f"\n✅ SUCCESS! Master Admin '{name}' has been created securely.")
        print("You can now use these credentials to log into the Admin Dashboard.")
        print("====================================\n")
        
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_master_admin()