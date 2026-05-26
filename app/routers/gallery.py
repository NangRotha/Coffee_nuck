from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime
from .. import schemas, models, auth
from ..database import get_db

router = APIRouter(prefix="/api/gallery", tags=["Gallery"])

UPLOAD_DIR = "app/uploads/gallery"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/", response_model=List[schemas.GalleryResponse])
def get_gallery(
    limit: Optional[int] = Query(None, description="Limit number of images"),
    db: Session = Depends(get_db)
):
    """Get all gallery images ordered by index"""
    query = db.query(models.Gallery).order_by(models.Gallery.order_index)
    
    if limit:
        query = query.limit(limit)
    
    return query.all()

@router.get("/{gallery_id}", response_model=schemas.GalleryResponse)
def get_gallery_image(gallery_id: int, db: Session = Depends(get_db)):
    """Get a specific gallery image by ID"""
    gallery = db.query(models.Gallery).filter(models.Gallery.id == gallery_id).first()
    if not gallery:
        raise HTTPException(status_code=404, detail="Gallery image not found")
    return gallery

@router.post("/", response_model=schemas.GalleryResponse)
def add_gallery_image(
    gallery_data: schemas.GalleryCreate,
    current_user: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    """Add a new gallery image (Admin only)"""
    gallery = models.Gallery(**gallery_data.dict())
    db.add(gallery)
    db.commit()
    db.refresh(gallery)
    return gallery

@router.put("/{gallery_id}", response_model=schemas.GalleryResponse)
def update_gallery_image(
    gallery_id: int,
    gallery_data: schemas.GalleryCreate,
    current_user: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    """Update gallery image information (Admin only)"""
    gallery = db.query(models.Gallery).filter(models.Gallery.id == gallery_id).first()
    if not gallery:
        raise HTTPException(status_code=404, detail="Gallery image not found")
    
    for key, value in gallery_data.dict(exclude_unset=True).items():
        setattr(gallery, key, value)
    
    db.commit()
    db.refresh(gallery)
    return gallery

@router.delete("/{gallery_id}")
def delete_gallery_image(
    gallery_id: int,
    current_user: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete a gallery image (Admin only)"""
    gallery = db.query(models.Gallery).filter(models.Gallery.id == gallery_id).first()
    if not gallery:
        raise HTTPException(status_code=404, detail="Gallery image not found")
    
    # Delete image file if exists
    if gallery.image_url and os.path.exists(gallery.image_url.replace("/uploads/", "app/uploads/")):
        try:
            os.remove(gallery.image_url.replace("/uploads/", "app/uploads/"))
        except:
            pass
    
    db.delete(gallery)
    db.commit()
    return {"message": "Gallery image deleted successfully"}

@router.post("/upload-image")
def upload_gallery_image(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_admin)
):
    """Upload gallery image (Admin only)"""
    # Validate file type
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (max 10MB for gallery)
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=400, detail="File too large. Max 10MB")
    
    # Generate unique filename
    timestamp = int(datetime.now().timestamp())
    filename = f"gallery_{timestamp}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"image_url": f"/uploads/gallery/{filename}"}

@router.post("/reorder")
def reorder_gallery(
    image_ids: List[int],
    current_user: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    """Reorder gallery images (Admin only)"""
    for index, image_id in enumerate(image_ids):
        gallery = db.query(models.Gallery).filter(models.Gallery.id == image_id).first()
        if gallery:
            gallery.order_index = index
    
    db.commit()
    return {"message": "Gallery order updated successfully"}

@router.post("/bulk-delete")
def bulk_delete_gallery(
    image_ids: List[int],
    current_user: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete multiple gallery images at once (Admin only)"""
    deleted_count = 0
    
    for image_id in image_ids:
        gallery = db.query(models.Gallery).filter(models.Gallery.id == image_id).first()
        if gallery:
            # Delete image file
            if gallery.image_url and os.path.exists(gallery.image_url.replace("/uploads/", "app/uploads/")):
                try:
                    os.remove(gallery.image_url.replace("/uploads/", "app/uploads/"))
                except:
                    pass
            
            db.delete(gallery)
            deleted_count += 1
    
    db.commit()
    
    return {
        "message": f"Successfully deleted {deleted_count} gallery images",
        "deleted_count": deleted_count
    }