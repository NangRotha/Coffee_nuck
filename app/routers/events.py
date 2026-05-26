from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime
from .. import schemas, models, auth
from ..database import get_db

router = APIRouter(prefix="/api/events", tags=["Events"])

UPLOAD_DIR = "app/uploads/events"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/", response_model=List[schemas.EventResponse])
def get_events(
    active_only: bool = Query(False, description="Get only active events"),
    limit: Optional[int] = Query(None, description="Limit number of events"),
    db: Session = Depends(get_db)
):
    """Get all events or filter by active status"""
    query = db.query(models.Event)
    
    if active_only:
        query = query.filter(models.Event.is_active == True)
        query = query.filter(models.Event.event_date >= datetime.now())
    
    query = query.order_by(models.Event.event_date.desc())
    
    if limit:
        query = query.limit(limit)
    
    return query.all()

@router.get("/upcoming", response_model=List[schemas.EventResponse])
def get_upcoming_events(
    limit: Optional[int] = Query(5, description="Limit number of events"),
    db: Session = Depends(get_db)
):
    """Get upcoming events only"""
    now = datetime.now()
    events = db.query(models.Event).filter(
        models.Event.is_active == True,
        models.Event.event_date >= now
    ).order_by(models.Event.event_date.asc()).limit(limit).all()
    return events

@router.get("/{event_id}", response_model=schemas.EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get a specific event by ID"""
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.post("/", response_model=schemas.EventResponse)
def create_event(
    event_data: schemas.EventCreate,
    current_user: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new event (Admin only)"""
    event = models.Event(**event_data.dict())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

@router.put("/{event_id}", response_model=schemas.EventResponse)
def update_event(
    event_id: int,
    event_data: schemas.EventUpdate,
    current_user: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    """Update event information (Admin only)"""
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    for key, value in event_data.dict(exclude_unset=True).items():
        setattr(event, key, value)
    
    db.commit()
    db.refresh(event)
    return event

@router.delete("/{event_id}")
def delete_event(
    event_id: int,
    current_user: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete an event (Admin only)"""
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Delete image file if exists
    if event.image and os.path.exists(event.image.replace("/uploads/", "app/uploads/")):
        try:
            os.remove(event.image.replace("/uploads/", "app/uploads/"))
        except:
            pass
    
    db.delete(event)
    db.commit()
    return {"message": "Event deleted successfully"}

@router.post("/upload-image")
def upload_event_image(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_admin)
):
    """Upload event image (Admin only)"""
    # Validate file type
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (max 5MB)
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(status_code=400, detail="File too large. Max 5MB")
    
    # Generate unique filename
    timestamp = int(datetime.now().timestamp())
    filename = f"event_{timestamp}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"image_url": f"/uploads/events/{filename}"}

@router.post("/{event_id}/toggle-status")
def toggle_event_status(
    event_id: int,
    current_user: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    """Toggle event active status (Admin only)"""
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    event.is_active = not event.is_active
    db.commit()
    
    return {
        "message": f"Event status updated to {'active' if event.is_active else 'inactive'}",
        "is_active": event.is_active
    }