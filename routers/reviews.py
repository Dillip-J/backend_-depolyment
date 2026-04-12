from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from database import get_db
import models, schemas

# 🚨 IMPORT THE BOUNCER
from dependencies import get_current_user 

router = APIRouter(prefix="/reviews", tags=["Reviews"])

# ==========================================
# 1. CREATE A REVIEW
# ==========================================
@router.post("/", response_model=schemas.ReviewOut)
def create_review(
    review: schemas.ReviewCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user) # 🔒 SECURED
):
    # 1. Check if booking exists and belongs to this exact user
    booking = db.query(models.Booking).filter(
        models.Booking.booking_id == review.booking_id, 
        models.Booking.user_id == current_user.user_id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found or not authorized.")
        
    # 🚨 THE FIX: The Time Traveler Loophole
    if booking.booking_status != "completed":
        raise HTTPException(status_code=400, detail="You can only review completed appointments.")
    
    # 2. Check if already reviewed
    existing_review = db.query(models.Review).filter(models.Review.booking_id == review.booking_id).first()
    if existing_review:
        raise HTTPException(status_code=400, detail="You have already reviewed this booking.")

    # 3. Save to DB
    new_review = models.Review(
        booking_id=review.booking_id,
        rating=review.rating,
        comment=review.comment
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review

# ==========================================
# 2. GET DOCTOR'S REVIEWS (Public)
# ==========================================
@router.get("/provider/{provider_id}")
def get_provider_reviews(provider_id: str, db: Session = Depends(get_db)):
    # 🚨 THE FIX: The Anonymous Ghost Trap
    # We join the Booking AND the User so we can grab the patient's actual name!
    reviews = db.query(models.Review)\
        .join(models.Booking)\
        .options(
            joinedload(models.Review.booking)
            .joinedload(models.Booking.user)
        )\
        .filter(models.Booking.provider_id == provider_id)\
        .order_by(models.Review.created_at.desc())\
        .all()
        
    # Format the data perfectly for the frontend profile cards
    formatted_reviews = []
    for r in reviews:
        formatted_reviews.append({
            "review_id": r.review_id,
            "rating": r.rating,
            "comment": r.comment,
            "date": r.created_at.strftime("%d %b, %Y") if hasattr(r, 'created_at') and r.created_at else "Recent",
            # Extract the user's name safely
            "patient_name": r.booking.user.name if r.booking and r.booking.user else "Anonymous Patient"
        })
        
    return formatted_reviews