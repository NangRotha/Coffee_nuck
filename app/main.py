from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os
from datetime import datetime, date, timedelta
from . import models, database
from . import auth as auth_module
from .database import engine, SessionLocal, get_db
from .config import config
from .routers import (
    auth,
    products,
    orders,
    staff,
    events,
    gallery,
    settings,
    payment
)

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Create default admin user if not exists
def create_default_admin():
    db = SessionLocal()
    try:
        existing_admin = db.query(models.User).filter(models.User.username == config.ADMIN_USERNAME).first()
        if not existing_admin:
            admin = models.User(
                username=config.ADMIN_USERNAME,
                password_hash=auth_module.get_password_hash(config.ADMIN_PASSWORD),
                full_name="Admin",
                role=models.UserRole.ADMIN
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()

create_default_admin()

def create_sample_events():
    db = SessionLocal()
    try:
        existing_count = db.query(models.Event).count()
        if existing_count == 0:
            sample_events = [
                models.Event(
                    title="Summer Coffee Festival",
                    description="Join us for our annual Summer Coffee Festival! Enjoy 20% off all drinks and live music from local artists.",
                    event_date=datetime.now() + timedelta(days=7),
                    discount_percent=20,
                    is_active=True
                ),
                models.Event(
                    title="Latte Art Workshop",
                    description="Learn the art of latte from our expert baristas. Limited seats available for hands-on training.",
                    event_date=datetime.now() + timedelta(days=14),
                    discount_percent=10,
                    is_active=True
                ),
            ]
            db.add_all(sample_events)
            db.commit()
    finally:
        db.close()

create_sample_events()

def create_sample_products():
    db = SessionLocal()
    try:
        existing_count = db.query(models.Product).count()
        if existing_count == 0:
            sample_products = [
                models.Product(name="Espresso", description="Strong and bold coffee shot", price=2.50, category="Coffee", status=models.ProductStatus.IN_STOCK, stock_quantity=50),
                models.Product(name="Cappuccino", description="Espresso with steamed milk foam", price=3.50, category="Coffee", status=models.ProductStatus.IN_STOCK, stock_quantity=45),
                models.Product(name="Latte", description="Smooth coffee with steamed milk", price=4.00, discount_price=3.50, category="Coffee", status=models.ProductStatus.IN_STOCK, stock_quantity=40),
                models.Product(name="Croissant", description="Buttery flaky pastry", price=3.00, category="Pastry", status=models.ProductStatus.IN_STOCK, stock_quantity=30),
            ]
            db.add_all(sample_products)
            db.commit()
    finally:
        db.close()

create_sample_products()

def create_sample_staff():
    db = SessionLocal()
    try:
        existing_count = db.query(models.Staff).count()
        if existing_count == 0:
            sample_staff = [
                models.Staff(name="John Barista", position="Head Barista", is_manager=True, order_index=0),
                models.Staff(name="Jane Smith", position="Coffee Specialist", is_manager=False, order_index=1),
            ]
            db.add_all(sample_staff)
            db.commit()
    finally:
        db.close()

create_sample_staff()

app = FastAPI(
    title="Coffee Shop API",
    description="API for Coffee Shop Management System",
    version="1.0.0"
)

# CORS middleware - Allow frontend apps to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Frontend User (Vite default)
        "http://localhost:5174",  # Frontend Admin (Vite default)
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "*"  # For development only - restrict in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directories if they don't exist
UPLOAD_DIRS = [
    "app/uploads/products",
    "app/uploads/staff",
    "app/uploads/events",
    "app/uploads/gallery",
    "app/uploads/settings"
]

for dir_path in UPLOAD_DIRS:
    os.makedirs(dir_path, exist_ok=True)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")

# Include routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(staff.router)
app.include_router(events.router)
app.include_router(gallery.router)
app.include_router(settings.router)
app.include_router(payment.router)

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "☕ Welcome to Coffee Shop API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "auth": "/api/auth",
            "products": "/api/products",
            "orders": "/api/orders",
            "staff": "/api/staff",
            "events": "/api/events",
            "gallery": "/api/gallery",
            "settings": "/api/settings",
            "payment": "/api/payment"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/statistics")
def get_statistics(db: Session = Depends(get_db)):
    """Get shop statistics for dashboard"""
    from sqlalchemy import func
    from . import models
    
    # Get counts
    total_products = db.query(func.count(models.Product.id)).scalar() or 0
    total_orders = db.query(func.count(models.Order.id)).scalar() or 0
    total_staff = db.query(func.count(models.Staff.id)).scalar() or 0
    total_events = db.query(func.count(models.Event.id)).filter(
        models.Event.is_active == True
    ).scalar() or 0
    
    # Today's sales
    today = date.today()
    today_sales_result = db.query(func.sum(models.Order.total_amount)).filter(
        models.Order.created_at >= today,
        models.Order.status == models.OrderStatus.PAID
    ).scalar()
    today_sales = float(today_sales_result) if today_sales_result else 0
    
    # This month sales
    first_day_of_month = date(today.year, today.month, 1)
    monthly_sales_result = db.query(func.sum(models.Order.total_amount)).filter(
        models.Order.created_at >= first_day_of_month,
        models.Order.status == models.OrderStatus.PAID
    ).scalar()
    monthly_sales = float(monthly_sales_result) if monthly_sales_result else 0
    
    # Low stock products
    low_stock = db.query(models.Product).filter(
        models.Product.stock_quantity < 10,
        models.Product.stock_quantity > 0,
        models.Product.status == models.ProductStatus.IN_STOCK
    ).count()
    
    out_of_stock = db.query(models.Product).filter(
        models.Product.status == models.ProductStatus.OUT_OF_STOCK
    ).count()
    
    # Pending orders
    pending_orders = db.query(models.Order).filter(
        models.Order.status == models.OrderStatus.PENDING
    ).count()
    
    # Recent orders (last 7 days)
    from datetime import timedelta
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_orders = db.query(models.Order).filter(
        models.Order.created_at >= seven_days_ago
    ).count()
    
    return {
        "total_products": total_products,
        "total_orders": total_orders,
        "total_staff": total_staff,
        "total_events": total_events,
        "today_sales": today_sales,
        "monthly_sales": monthly_sales,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "pending_orders": pending_orders,
        "recent_orders": recent_orders
    }

@app.get("/api/dashboard/chart-data")
def get_chart_data(db: Session = Depends(get_db)):
    """Get chart data for dashboard"""
    from sqlalchemy import func
    from . import models
    from datetime import timedelta
    
    # Last 7 days sales
    chart_data = []
    today = date.today()
    
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        next_day = day + timedelta(days=1)
        
        daily_sales = db.query(func.sum(models.Order.total_amount)).filter(
            models.Order.created_at >= day,
            models.Order.created_at < next_day,
            models.Order.status == models.OrderStatus.PAID
        ).scalar() or 0
        
        order_count = db.query(func.count(models.Order.id)).filter(
            models.Order.created_at >= day,
            models.Order.created_at < next_day
        ).scalar() or 0
        
        chart_data.append({
            "date": day.strftime("%Y-%m-%d"),
            "sales": float(daily_sales),
            "orders": order_count
        })
    
    return chart_data