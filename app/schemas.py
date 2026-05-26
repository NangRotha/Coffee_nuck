from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    STAFF = "staff"

class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ProductStatus(str, Enum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"

# User Schemas
class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: UserRole = UserRole.STAFF

class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    role: UserRole
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# Product Schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    discount_price: float = 0
    image: Optional[str] = None
    category: str
    status: ProductStatus = ProductStatus.IN_STOCK
    stock_quantity: int = 0

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    discount_price: Optional[float] = None
    image: Optional[str] = None
    category: Optional[str] = None
    status: Optional[ProductStatus] = None
    stock_quantity: Optional[int] = None

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Order Item Schemas
class OrderItemCreate(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    price: float

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    price: float
    
    class Config:
        from_attributes = True

# Order Schemas
class OrderCreate(BaseModel):
    customer_name: str
    customer_phone: str
    customer_telegram_id: Optional[str] = None
    items: List[OrderItemCreate]
    notes: Optional[str] = None

class OrderResponse(BaseModel):
    id: int
    transaction_id: str
    customer_name: str
    customer_phone: str
    total_amount: float
    status: OrderStatus
    payment_qr: Optional[str] = None
    qr_url: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    paid_at: Optional[datetime] = None
    items: List[OrderItemResponse]
    
    class Config:
        from_attributes = True

# Staff Schemas
class StaffBase(BaseModel):
    name: str
    position: str
    bio: Optional[str] = None
    image: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_manager: bool = False
    order_index: int = 0

class StaffCreate(StaffBase):
    pass

class StaffUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[str] = None
    bio: Optional[str] = None
    image: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_manager: Optional[bool] = None
    order_index: Optional[int] = None

class StaffResponse(StaffBase):
    id: int
    
    class Config:
        from_attributes = True

# Event Schemas
class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    image: Optional[str] = None
    event_date: datetime
    discount_percent: float = 0
    is_active: bool = True

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    event_date: Optional[datetime] = None
    discount_percent: Optional[float] = None
    is_active: Optional[bool] = None

class EventResponse(EventBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Gallery Schemas
class GalleryBase(BaseModel):
    image_url: str
    title: Optional[str] = None
    order_index: int = 0

class GalleryCreate(GalleryBase):
    pass

class GalleryResponse(GalleryBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Shop Settings Schemas
class ShopSettingResponse(BaseModel):
    id: int
    shop_name: str
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    opening_hours: Optional[str] = None
    about_text: Optional[str] = None
    
    class Config:
        from_attributes = True

class ShopSettingUpdate(BaseModel):
    shop_name: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    opening_hours: Optional[str] = None
    about_text: Optional[str] = None

# Promotion Schemas
class PromotionBase(BaseModel):
    code: str
    description: str
    discount_percent: float
    valid_from: datetime
    valid_to: datetime
    is_active: bool = True

class PromotionCreate(PromotionBase):
    pass

class PromotionResponse(PromotionBase):
    id: int
    
    class Config:
        from_attributes = True

# Payment Schemas
class PaymentRequest(BaseModel):
    order_id: int

class PaymentResponse(BaseModel):
    qr_data: str
    qr_url: str
    transaction_id: str

class VerifyPayment(BaseModel):
    transaction_id: str