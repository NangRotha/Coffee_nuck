import hashlib
import hmac
import httpx
from datetime import datetime
from .config import config

def generate_khqr_hash(transaction_id: str, amount: float, success_url: str, remark: str) -> str:
    """Generate SHA1 hash for KHQR payment"""
    raw_string = f"{config.KHQR_SECRET_KEY}{transaction_id}{amount}{success_url}{remark}"
    return hashlib.sha1(raw_string.encode()).hexdigest()

def generate_verify_hash(transaction_id: str) -> str:
    """Generate SHA1 hash for transaction verification"""
    raw_string = f"{config.KHQR_SECRET_KEY}{transaction_id}"
    return hashlib.sha1(raw_string.encode()).hexdigest()

async def send_telegram_message(chat_id: str, message: str):
    """Send message via Telegram bot"""
    try:
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
            )
            return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

async def send_payment_notification(order_data: dict):
    """Send payment notification to admin and customer"""
    
    # Admin notification
    admin_message = f"""
🏪 <b>New Coffee Order!</b>
━━━━━━━━━━━━━━━━
🧾 Order ID: <code>{order_data['transaction_id']}</code>
👤 Customer: {order_data['customer_name']}
📞 Phone: {order_data['customer_phone']}
💰 Amount: <b>${order_data['total_amount']:.2f}</b>
🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━
📝 <b>Items:</b>
{order_data['items_text']}
    """
    await send_telegram_message(config.TELEGRAM_ADMIN_ID, admin_message)
    
    # Customer notification if telegram_id provided
    if order_data.get('customer_telegram_id'):
        customer_message = f"""
☕ <b>Order Confirmed!</b>
━━━━━━━━━━━━━━━━
Thank you for ordering from Coffee Shop!

🧾 Order ID: <code>{order_data['transaction_id']}</code>
💰 Amount: <b>${order_data['total_amount']:.2f}</b>

⏳ Your order is being prepared.
We'll notify you when it's ready!

Thank you for choosing us! ❤️
        """
        await send_telegram_message(order_data['customer_telegram_id'], customer_message)

async def send_payment_success_notification(order_data: dict):
    """Send payment success notification"""
    
    # Admin notification
    admin_message = f"""
✅ <b>Payment Success!</b>
━━━━━━━━━━━━━━━━
🧾 Order ID: <code>{order_data['transaction_id']}</code>
💰 Amount: <b>${order_data['total_amount']:.2f}</b>
✅ Status: PAID
🕐 Paid at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    await send_telegram_message(config.TELEGRAM_ADMIN_ID, admin_message)
    
    # Customer notification
    if order_data.get('customer_telegram_id'):
        customer_message = f"""
✅ <b>Payment Successful!</b>
━━━━━━━━━━━━━━━━
Thank you for your payment!

🧾 Order ID: <code>{order_data['transaction_id']}</code>
💰 Amount Paid: <b>${order_data['total_amount']:.2f}</b>

☕ Your coffee will be ready soon!
We'll notify you when it's ready for pickup.

Thank you for choosing us! ❤️
        """
        await send_telegram_message(order_data['customer_telegram_id'], customer_message)