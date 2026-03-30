#routers/reviews.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Review, Booking
import schemas
from routers.auth import get_current_user # Your patient auth dependency

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.post("/", response_model=schemas.ReviewOut)
def create_review(review: schemas.ReviewCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # 1. Check if booking exists and belongs to this user
    booking = db.query(Booking).filter(Booking.booking_id == review.booking_id, Booking.user_id == current_user.user_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found or not authorized.")
    
    # 2. Check if already reviewed
    existing_review = db.query(Review).filter(Review.booking_id == review.booking_id).first()
    if existing_review:
        raise HTTPException(status_code=400, detail="You have already reviewed this booking.")

    # 3. Save to DB
    new_review = Review(
        booking_id=review.booking_id,
        rating=review.rating,
        comment=review.comment
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review

@router.get("/provider/{provider_id}")
def get_provider_reviews(provider_id: str, db: Session = Depends(get_db)):
    # Join Reviews with Bookings to get all reviews for a specific doctor
    reviews = db.query(Review).join(Booking).filter(Booking.provider_id == provider_id).all()
    return reviews