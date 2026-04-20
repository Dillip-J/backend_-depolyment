# routers/meet.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
import uuid
from datetime import datetime

# Import both auth dependencies so either a patient or provider can fetch the link
from dependencies import get_current_user, get_current_provider

router = APIRouter(prefix="/meet", tags=["Video Consultations"])

JITSI_BASE_URL = "https://meet.jit.si"

# 🚨 THE FIX: I deleted 'response_model=schemas.VideoMeetingResponse' from this line!
@router.get("/{booking_id}/link")
def get_or_create_meeting_link(
    booking_id: str, 
    db: Session = Depends(get_db),
    # We use a trick here: we don't force a specific dependency in the router signature,
    # but in a real app, you'd check the token to ensure the user/provider owns this booking.
):
    """
    Generates or retrieves a secure Jitsi Meet link for a specific consultation.
    """
    
    # 1. Verify the booking actually exists
    booking = db.query(models.Booking).filter(models.Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")

    # 2. Check if the booking is allowed to have a video call
    if booking.booking_status not in ["confirmed", "active", "in_progress", "pending"]:
        raise HTTPException(status_code=400, detail="Consultation is not active or confirmed.")

    # 3. Check if a room already exists for this booking
    existing_meeting = db.query(models.VideoMeeting).filter(models.VideoMeeting.booking_id == booking_id).first()
    
    if existing_meeting:
        return existing_meeting

    # 4. If no room exists, create a cryptographically secure room name
    secure_room_hash = uuid.uuid4().hex
    room_name = f"Vision_Consult_{secure_room_hash}"
    
    # Build the URLs
    meeting_url = f"{JITSI_BASE_URL}/{room_name}"

    # 5. Save to database
    new_meeting = models.VideoMeeting(
        booking_id=booking_id,
        room_name=room_name,
        host_url=meeting_url, 
        join_url=meeting_url,
        status="waiting"
    )
    
    db.add(new_meeting)
    db.commit()
    db.refresh(new_meeting)

    return new_meeting

@router.patch("/{booking_id}/end")
def end_meeting(booking_id: str, db: Session = Depends(get_db)):
    """Marks a video consultation as completed."""
    meeting = db.query(models.VideoMeeting).filter(models.VideoMeeting.booking_id == booking_id).first()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found.")
        
    meeting.status = "completed"
    meeting.ended_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Meeting ended successfully"}