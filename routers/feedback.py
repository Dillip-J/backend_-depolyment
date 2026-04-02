# routers/feedback.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import get_db
import models
from schemas import ReviewCreate, ComplaintCreate
from dependencies import get_current_user

router = APIRouter(prefix="/feedback", tags=["Reviews & Complaints"])

@router.post("/review", status_code=status.HTTP_201_CREATED)
def post_review(
    review_data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)  # Requires login
):
    try:
        new_review = models.Review(
            booking_id=review_data.booking_id,
            rating=review_data.rating,
            comment=review_data.comment
        )
        db.add(new_review)
        db.commit()
        db.refresh(new_review)
        return {"message": "Review submitted", "review_id": new_review.review_id}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Review already exists for this booking")

@router.post("/complaint", status_code=status.HTTP_201_CREATED)
def file_complaint(
    complaint_data: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)  # Requires login — provides user_id
):
    # Look up the booking to get the provider_id securely from the DB
    booking = db.query(models.Booking).filter(
        models.Booking.booking_id == complaint_data.booking_id,
        models.Booking.user_id == current_user.user_id  # Ensure it's the user's own booking
    ).first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found or does not belong to you.")

    new_complaint = models.Complaint(
        booking_id=complaint_data.booking_id,
        user_id=current_user.user_id,       # Comes from JWT, not request body
        provider_id=booking.provider_id,    # Fetched from DB, not request body
        complaint_text=complaint_data.complaint_text
    )
    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)
    return {"message": "Complaint filed successfully", "complaint_id": new_complaint.complaint_id}
# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from sqlalchemy.exc import IntegrityError
# from database import get_db
# from models import Review, Complaint
# from schemas import ReviewCreate, ComplaintCreate

# router = APIRouter(prefix="/feedback", tags=["Reviews & Complaints"])

# @router.post("/review", status_code=status.HTTP_201_CREATED)
# def post_review(review_data: ReviewCreate, db: Session = Depends(get_db)):
#     try:
#         new_review = Review(
#             booking_id=review_data.booking_id,
#             rating=review_data.rating,
#             comment=review_data.comment
#         )
#         db.add(new_review)
#         db.commit()
#         db.refresh(new_review)
#         return {"message": "Review submitted", "review_id": new_review.review_id}
    
#     except IntegrityError:
#         db.rollback()
#         # This triggers if a review for the booking_id already exists (Unique constraint)
#         raise HTTPException(status_code=400, detail="Review already exists for this booking")

# @router.post("/complaint", status_code=status.HTTP_201_CREATED)
# def file_complaint(complaint_data: ComplaintCreate, db: Session = Depends(get_db)):
#     new_complaint = Complaint(
#         booking_id=complaint_data.booking_id,
#         user_id=complaint_data.user_id,
#         provider_id=complaint_data.provider_id,
#         complaint_text=complaint_data.complaint_text
#     )
#     db.add(new_complaint)
#     db.commit()
#     db.refresh(new_complaint)
#     return {"message": "Complaint filed successfully", "complaint_id": new_complaint.complaint_id}