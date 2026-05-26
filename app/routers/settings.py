from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import os
import shutil
from datetime import datetime
from .. import schemas, models, auth
from ..database import get_db

router = APIRouter(prefix="/api/settings", tags=["Settings"])

UPLOAD_DIR = "app/uploads/settings"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/", response_model=schemas.ShopSettingResponse)
def get_settings(db: Session = Depends(get_db)):
    """Get shop settings"""
    settings = db.query(models.ShopSetting).first()
    if not settings:
        # Create default settings
        settings = models.ShopSetting(
            shop_name="Coffee Shop",
            address="123 Street, Phnom Penh, Cambodia",
            phone="+855 12 345 678",
            email="info@coffeeshop.com",
            opening_hours="Mon-Sun: 7:00 AM - 9:00 PM",
            about_text="Welcome to our coffee shop! We serve the finest coffee in town."
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@router.put("/", response_model=schemas.ShopSettingResponse)
def update_settings(
    settings_data: schemas.ShopSettingUpdate,
    current_user: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    """Update shop settings (Admin only)"""
    settings = db.query(models.ShopSetting).first()
    if not settings:
        settings = models.ShopSetting()
        db.add(settings)
    
    for key, value in settings_data.dict(exclude_unset=True).items():
        setattr(settings, key, value)
    
    db.commit()
    db.refresh(settings)
    return settings

@router.post("/upload-logo")
def upload_logo(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    """Upload shop logo (Admin only)"""
    # Validate file type
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Generate unique filename
    filename = f"logo_{datetime.now().timestamp()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update settings
    settings = db.query(models.ShopSetting).first()
    if settings:
        settings.logo_url = f"/uploads/settings/{filename}"
        db.commit()
    
    return {"logo_url": f"/uploads/settings/{filename}"}

@router.post("/upload-banner")
def upload_banner(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    """Upload shop banner (Admin only)"""
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    filename = f"banner_{datetime.now().timestamp()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    settings = db.query(models.ShopSetting).first()
    if settings:
        settings.banner_url = f"/uploads/settings/{filename}"
        db.commit()
    
    return {"banner_url": f"/uploads/settings/{filename}"}