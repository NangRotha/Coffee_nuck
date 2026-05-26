from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import secrets
from datetime import datetime
from .. import schemas, models, auth, utils
from ..database import get_db

router = APIRouter(prefix="/api/orders", tags=["Orders"])

def generate_transaction_id():
    return f"COF_{int(datetime.now().timestamp())}_{secrets.token_hex(4)}"

@router.post("/", response_model=schemas.OrderResponse)
async def create_order(
    order_data: schemas.OrderCreate,
    db: Session = Depends(get_db)
):
    # Generate transaction ID
    transaction_id = generate_transaction_id()
    
    # Calculate total amount
    total_amount = sum(item.price * item.quantity for item in order_data.items)
    
    # Check stock
    for item in order_data.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if product and product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Not enough stock for {product.name}. Available: {product.stock_quantity}"
            )
    
    # Create order
    order = models.Order(
        transaction_id=transaction_id,
        customer_name=order_data.customer_name,
        customer_phone=order_data.customer_phone,
        customer_telegram_id=order_data.customer_telegram_id,
        total_amount=total_amount,
        notes=order_data.notes,
        status=models.OrderStatus.PENDING
    )
    db.add(order)
    db.flush()
    
    # Create order items and update stock
    items_text = ""
    for item_data in order_data.items:
        order_item = models.OrderItem(
            order_id=order.id,
            product_id=item_data.product_id,
            product_name=item_data.product_name,
            quantity=item_data.quantity,
            price=item_data.price
        )
        db.add(order_item)
        
        # Update stock
        product = db.query(models.Product).filter(models.Product.id == item_data.product_id).first()
        if product:
            product.stock_quantity -= item_data.quantity
            if product.stock_quantity == 0:
                product.status = models.ProductStatus.OUT_OF_STOCK
        
        items_text += f"• {item_data.product_name} x{item_data.quantity} = ${item_data.price * item_data.quantity:.2f}\n"
    
    db.commit()
    db.refresh(order)
    
    # Send Telegram notification
    notification_data = {
        'transaction_id': transaction_id,
        'customer_name': order_data.customer_name,
        'customer_phone': order_data.customer_phone,
        'customer_telegram_id': order_data.customer_telegram_id,
        'total_amount': total_amount,
        'items_text': items_text
    }
    await utils.send_payment_notification(notification_data)
    
    # Get order with items
    result = db.query(models.Order).filter(models.Order.id == order.id).first()
    return result

@router.get("/", response_model=list[schemas.OrderResponse])
def get_orders(
    status: Optional[str] = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.Order)
    if status:
        query = query.filter(models.Order.status == status)
    return query.order_by(models.Order.created_at.desc()).all()

@router.get("/{order_id}", response_model=schemas.OrderResponse)
def get_order(
    order_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.put("/{order_id}/status")
async def update_order_status(
    order_id: int,
    status: schemas.OrderStatus,
    current_user: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    old_status = order.status
    order.status = status
    if status == schemas.OrderStatus.PAID:
        order.paid_at = datetime.utcnow()
    
    db.commit()
    
    # Send Telegram notification for status update
    if order.customer_telegram_id and old_status != status:
        status_messages = {
            schemas.OrderStatus.PROCESSING: "🔄 Your order is being prepared!",
            schemas.OrderStatus.COMPLETED: "✅ Your order is ready for pickup! 🎉",
            schemas.OrderStatus.CANCELLED: "❌ Your order has been cancelled."
        }
        if status in status_messages:
            message = f"""
{status_messages[status]}
━━━━━━━━━━━━━━━━
🧾 Order ID: <code>{order.transaction_id}</code>
☕ Thank you for choosing us!
            """
            await utils.send_telegram_message(order.customer_telegram_id, message)
    
    return {"message": "Order status updated successfully"}

@router.get("/reports/daily")
def get_daily_report(
    current_user: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    today = datetime.utcnow().date()
    orders = db.query(models.Order).filter(
        models.Order.created_at >= today,
        models.Order.status == models.OrderStatus.PAID
    ).all()
    
    total_sales = sum(order.total_amount for order in orders)
    
    return {
        "date": today,
        "total_orders": len(orders),
        "total_sales": total_sales,
        "orders": orders
    }