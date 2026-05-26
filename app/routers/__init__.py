# Import all routers
from .auth import router as auth_router
from .products import router as products_router
from .orders import router as orders_router
from .staff import router as staff_router
from .events import router as events_router
from .gallery import router as gallery_router
from .settings import router as settings_router
from .payment import router as payment_router

# Export all routers
__all__ = [
    'auth_router',
    'products_router', 
    'orders_router',
    'staff_router',
    'events_router',
    'gallery_router',
    'settings_router',
    'payment_router'
]