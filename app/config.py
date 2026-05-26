import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database - Use PostgreSQL on Render
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./coffee_shop.db")
    
    # JWT
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 1440
    
    # KHQR Payment
    KHQR_PROFILE_ID = os.getenv("KHQR_PROFILE_ID", "rw6pCtr5IESLTAIbxFsZwyy43u0DRM9y")
    KHQR_SECRET_KEY = os.getenv("KHQR_SECRET_KEY", "0SimZdqZL7Q0lADeeXlQsDRMtIZbilbt")
    KHQR_API_URL = "https://khqr.cc/api/rw6pCtr5IESLTAIbxFsZwyy43u0DRM9y/payment-gateway/v1/payments/qr-api"
    KHQR_CHECK_URL = "https://khqr.cc/api/rw6pCtr5IESLTAIbxFsZwyy43u0DRM9y/payment-gateway/v1/payments/check-trans"
    
    # Telegram
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8818890848:AAH-_8fHsBPQfWzX4hTjYRZNk-rifuonedg")
    TELEGRAM_ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID", "1422320012")
    
    # Admin Default Credentials
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

config = Config()