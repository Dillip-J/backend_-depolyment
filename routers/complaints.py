# routers/complaints.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Complaint, Booking
import schemas

# 🚨 FIX APPLIED: Importing the guards from our central dependencies file!
from dependencies import get_current_user, get_current_admin 

router = APIRouter(prefix="/complaints", tags=["Complaints"])

@router.post("/", response_model=schemas.ComplaintOut)
def create_complaint(complaint: schemas.ComplaintCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # 1. Verify Booking
    booking = db.query(Booking).filter(Booking.booking_id == complaint.booking_id, Booking.user_id == current_user.user_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")

    # 2. Save Complaint
    new_complaint = Complaint(
        booking_id=booking.booking_id,
        user_id=current_user.user_id,
        provider_id=booking.provider_id, 
        complaint_text=complaint.complaint_text,
        status="open"
    )
    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)
    return new_complaint

# --- ADMIN ONLY ROUTES ---

@router.get("/admin/all", dependencies=[Depends(get_current_admin)])
def get_all_complaints(db: Session = Depends(get_db)):
    # Admin views all complaints
    return db.query(Complaint).order_by(Complaint.status.desc()).all()

@router.patch("/admin/{complaint_id}/resolve", dependencies=[Depends(get_current_admin)])
def resolve_complaint(complaint_id: int, db: Session = Depends(get_db)):
    # Admin marks a complaint as resolved
    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found.")
    
    complaint.status = "resolved"
    db.commit()
    return {"message": "Complaint marked as resolved successfully."}