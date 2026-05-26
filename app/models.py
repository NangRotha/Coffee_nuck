from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    STAFF = "staff"

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ProductStatus(str, enum.Enum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(Enum(UserRole), default=UserRole.STAFF)
    created_at = Column(DateTime, default=datetime.utcnow)

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    discount_price = Column(Float, default=0)
    image = Column(String(255))
    category = Column(String(50))
    status = Column(Enum(ProductStatus), default=ProductStatus.IN_STOCK)
    stock_quantity = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(100), unique=True, index=True)
    customer_name = Column(String(100))
    customer_phone = Column(String(20))
    customer_telegram_id = Column(String(50))
    total_amount = Column(Float, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    payment_qr = Column(Text)
    qr_url = Column(String(500))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime)
    
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    product_name = Column(String(100))
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    
    order = relationship("Order", back_populates="items")

class Staff(Base):
    __tablename__ = "staff"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    position = Column(String(100))
    bio = Column(Text)
    image = Column(String(255))
    email = Column(String(100))
    phone = Column(String(20))
    is_manager = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    image = Column(String(255))
    event_date = Column(DateTime)
    discount_percent = Column(Float, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Gallery(Base):
    __tablename__ = "gallery"
    
    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String(255), nullable=False)
    title = Column(String(100))
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class ShopSetting(Base):
    __tablename__ = "shop_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_name = Column(String(100), default="Coffee Shop")
    logo_url = Column(String(255))
    banner_url = Column(String(255))
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(100))
    opening_hours = Column(String(200))
    about_text = Column(Text)

class Promotion(Base):
    __tablename__ = "promotions"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True)
    description = Column(Text)
    discount_percent = Column(Float)
    valid_from = Column(DateTime)
    valid_to = Column(DateTime)
    is_active = Column(Boolean, default=True)