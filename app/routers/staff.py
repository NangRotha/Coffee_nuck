from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from datetime import datetime
from .. import schemas, models, auth
from ..database import get_db

router = APIRouter(prefix="/api/staff", tags=["Staff"])

UPLOAD_DIR = "app/uploads/staff"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/", response_model=list[schemas.StaffResponse])
def get_staff(db: Session = Depends(get_db)):
    """Get all staff members"""
    return db.query(models.Staff).order_by(models.Staff.order_index).all()

@router.get("/{staff_id}", response_model=schemas.StaffResponse)
def get_staff_member(staff_id: int, db: Session = Depends(get_db)):
    """Get a specific staff member by ID"""
    staff = db.query(models.Staff).filter(models.Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    return staff

@router.post("/", response_model=schemas.StaffResponse)
def create_staff(
    staff_data: schemas.StaffCreate,
    current_user: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new staff member (Admin only)"""
    staff = models.Staff(**staff_data.dict())
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff

@router.put("/{staff_id}", response_model=schemas.StaffResponse)
def update_staff(
    staff_id: int,
    staff_data: schemas.StaffUpdate,
    current_user: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    """Update staff member information (Admin only)"""
    staff = db.query(models.Staff).filter(models.Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    for key, value in staff_data.dict(exclude_unset=True).items():
        setattr(staff, key, value)
    
    db.commit()
    db.refresh(staff)
    return staff

@router.delete("/{staff_id}")
def delete_staff(
    staff_id: int,
    current_user: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete a staff member (Admin only)"""
    staff = db.query(models.Staff).filter(models.Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    # Delete image file if exists
    if staff.image and os.path.exists(staff.image.replace("/uploads/", "app/uploads/")):
        try:
            os.remove(staff.image.replace("/uploads/", "app/uploads/"))
        except:
            pass
    
    db.delete(staff)
    db.commit()
    return {"message": "Staff deleted successfully"}

@router.post("/upload-image")
def upload_staff_image(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_admin)
):
    """Upload staff profile image (Admin only)"""
    # Validate file type
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: jpg, jpeg, png, gif, webp")
    
    # Generate unique filename
    filename = f"staff_{datetime.now().timestamp()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"image_url": f"/uploads/staff/{filename}"}

@router.post("/reorder")
def reorder_staff(
    staff_ids: List[int],
    current_user: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    """Reorder staff display order (Admin only)"""
    for index, staff_id in enumerate(staff_ids):
        staff = db.query(models.Staff).filter(models.Staff.id == staff_id).first()
        if staff:
            staff.order_index = index
    
    db.commit()
    return {"message": "Staff order updated successfully"}

@router.get("/managers/", response_model=list[schemas.StaffResponse])
def get_managers(db: Session = Depends(get_db)):
    """Get all managers only"""
    return db.query(models.Staff).filter(models.Staff.is_manager == True).order_by(models.Staff.order_index).all()