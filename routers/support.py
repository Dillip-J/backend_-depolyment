# routers/support.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import models

router = APIRouter(prefix="/support", tags=["Support"])

@router.get("/")
def get_support_page(db: Session = Depends(get_db)):
    # 1. Fetch support contacts
    support_staff = db.query(models.Admin).filter(models.Admin.role == "support").all()
    
    # 2. Example: Static FAQ list (You could also move this to a database table later)
    faqs = [
        {"question": "How do I cancel a booking?", "answer": "Go to your 'Bookings' tab and click cancel."},
        {"question": "Where can I see my reports?", "answer": "Reports are available in the 'Medical Records' section."}
    ]

    return {
        "header": "Help & Support",
        "system_status": "Online",  # Hardcoded or dynamic check
        "contacts": [
            {"name": s.name, "email": s.email} for s in support_staff
        ],
        "faqs": faqs
    }