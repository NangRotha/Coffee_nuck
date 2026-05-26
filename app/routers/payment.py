from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import httpx
import hashlib
from datetime import datetime
from .. import schemas, models, auth, utils
from ..database import get_db
from ..config import config

router = APIRouter(prefix="/api/payment", tags=["Payment"])

def generate_khqr_hash(transaction_id: str, amount: float, success_url: str, remark: str) -> str:
    """Generate SHA1 hash for KHQR payment"""
    raw_string = f"{config.KHQR_SECRET_KEY}{transaction_id}{amount}{success_url}{remark}"
    return hashlib.sha1(raw_string.encode()).hexdigest()

@router.post("/create-qr")
async def create_payment_qr(
    payment_data: schemas.PaymentRequest,
    db: Session = Depends(get_db)
):
    """Create KHQR payment QR code"""
    # Get order
    order = db.query(models.Order).filter(models.Order.id == payment_data.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    success_url = f"https://yourdomain.com/payment-success?order_id={order.id}"
    remark = f"Order {order.transaction_id}"
    
    # Generate hash
    payment_hash = generate_khqr_hash(
        order.transaction_id,
        order.total_amount,
        success_url,
        remark
    )
    
    # Prepare request data
    request_data = {
        "transaction_id": order.transaction_id,
        "amount": order.total_amount,
        "success_url": success_url,
        "remark": remark,
        "hash": payment_hash
    }
    
    # Call KHQR API
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                config.KHQR_API_URL,
                data=request_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("responseCode") == 0:
                    qr_data = result.get("data", {}).get("qr", "")
                    qr_url = result.get("data", {}).get("qr_url", "")
                    
                    # Update order with QR info
                    order.payment_qr = qr_data
                    order.qr_url = qr_url
                    db.commit()
                    
                    return {
                        "qr_data": qr_data,
                        "qr_url": qr_url,
                        "transaction_id": order.transaction_id,
                        "amount": order.total_amount
                    }
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Payment API error: {result.get('responseMessage')}"
                    )
            else:
                raise HTTPException(status_code=400, detail="Failed to create payment QR")
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Payment error: {str(e)}")

@router.post("/verify/{transaction_id}")
async def verify_payment(
    transaction_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Verify payment status"""
    # Generate verification hash
    verify_hash = hashlib.sha1(f"{config.KHQR_SECRET_KEY}{transaction_id}".encode()).hexdigest()
    
    # Call verification API
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                config.KHQR_CHECK_URL,
                data={
                    "transaction_id": transaction_id,
                    "hash": verify_hash
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("responseCode") == 0:
                    status = result.get("data", {}).get("status", "").lower()
                    amount = result.get("data", {}).get("amount", 0)
                    
                    if status == "success":
                        # Update order status
                        order = db.query(models.Order).filter(
                            models.Order.transaction_id == transaction_id
                        ).first()
                        
                        if order and order.status != models.OrderStatus.PAID:
                            order.status = models.OrderStatus.PAID
                            order.paid_at = datetime.utcnow()
                            db.commit()
                            
                            # Send success notification
                            order_data = {
                                'transaction_id': order.transaction_id,
                                'total_amount': order.total_amount,
                                'customer_telegram_id': order.customer_telegram_id
                            }
                            background_tasks.add_task(
                                utils.send_payment_success_notification,
                                order_data
                            )
                        
                        return {
                            "verified": True,
                            "status": "success",
                            "amount": amount,
                            "transaction_id": transaction_id
                        }
                
                return {
                    "verified": False,
                    "status": "pending",
                    "transaction_id": transaction_id
                }
            else:
                return {
                    "verified": False,
                    "status": "unknown",
                    "transaction_id": transaction_id
                }
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Verification error: {str(e)}")

@router.post("/webhook")
async def payment_webhook(request_data: dict, db: Session = Depends(get_db)):
    """KHQR payment webhook handler"""
    try:
        transaction_id = request_data.get("transaction_id")
        status = request_data.get("status", "").lower()
        amount = request_data.get("amount", 0)
        
        if status == "success" and transaction_id:
            order = db.query(models.Order).filter(
                models.Order.transaction_id == transaction_id
            ).first()
            
            if order and order.status != models.OrderStatus.PAID:
                order.status = models.OrderStatus.PAID
                order.paid_at = datetime.utcnow()
                db.commit()
                
                # Send notification
                order_data = {
                    'transaction_id': order.transaction_id,
                    'total_amount': order.total_amount,
                    'customer_telegram_id': order.customer_telegram_id
                }
                await utils.send_payment_success_notification(order_data)
                
                return {"status": "success", "message": "Order updated"}
        
        return {"status": "ok"}
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}