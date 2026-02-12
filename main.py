import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Telegram Notification Backend")

# ---------------------- CORS Middleware (MUST BE FIRST) ----------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://followerssupply.store",
        "https://www.followerssupply.store"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------- Environment Variables ----------------------
# Different bots for different notifications (as per your original setup)
BOT_TOKEN_NEW_USER = os.getenv("BOT_TOKEN_NEW_USER")
BOT_TOKEN_QR = os.getenv("BOT_TOKEN_QR")          # Used for QR, payment started, payment ended
BOT_TOKEN_ORDER = os.getenv("BOT_TOKEN_ORDER")
CHAT_ID = os.getenv("CHAT_ID")

# ---------------------- Pydantic Models (Request Bodies) ----------------------
class NewUserNotification(BaseModel):
    username: str
    mobile: str
    ip: str
    profile_status: str

class QRPaymentStarted(BaseModel):
    username: str
    mobile: str
    package: str
    amount: str
    ip: str
    is_special: bool

class PaymentStarted(BaseModel):
    username: str
    mobile: str
    package: str
    amount: str
    ip: str
    method: str

class PaymentTimeEnded(BaseModel):
    username: str
    mobile: str
    package: str
    amount: str
    ip: str
    method: str

class OrderNotification(BaseModel):
    username: str
    mobile: str
    package: str
    price: int
    ip: str

# ---------------------- Helper Function: Send Telegram Message ----------------------
async def send_telegram(bot_token: str, chat_id: str, text: str, parse_mode: str = "HTML"):
    """
    Send a message to Telegram via bot API.
    """
    if not bot_token or not chat_id:
        raise HTTPException(status_code=500, detail="Missing Telegram credentials")
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=10.0)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Telegram API error: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# ---------------------- API Endpoints ----------------------

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "Telegram Notifier"}

@app.post("/api/notify/new-user")
async def notify_new_user(data: NewUserNotification):
    """
    Send notification when a new user submits username & mobile.
    Uses BOT_TOKEN_NEW_USER.
    """
    text = (
        f"🔔 New User Submitted\n"
        f"👤 Username: {data.username}\n"
        f"📱 Mobile: {data.mobile}\n"
        f"🌐 IP: {data.ip}\n"
        f"📊 Status: {data.profile_status}"
    )
    result = await send_telegram(BOT_TOKEN_NEW_USER, CHAT_ID, text)
    return {"success": True, "telegram_response": result}

@app.post("/api/notify/qr-payment-started")
async def notify_qr_payment_started(data: QRPaymentStarted):
    """
    Send notification when QR payment modal is opened.
    Uses BOT_TOKEN_QR.
    """
    special_text = "YES" if data.is_special else "NO"
    text = (
        f"📲 <b>QR PAYMENT STARTED 🎉</b>\n"
        f"👤 Username: <code>{data.username or 'Unknown'}</code>\n"
        f"📱 Mobile: <code>{data.mobile or 'Not Provided'}</code>\n"
        f"📦 Package: <code>{data.package}</code>\n"
        f"💰 Amount: <code>{data.amount}</code>\n"
        f"🌐 IP: <code>{data.ip}</code>\n"
        f"💎 Special User: <b>{special_text}</b>"
    )
    result = await send_telegram(BOT_TOKEN_QR, CHAT_ID, text, parse_mode="HTML")
    return {"success": True, "telegram_response": result}

@app.post("/api/notify/payment-started")
async def notify_payment_started(data: PaymentStarted):
    """
    Send notification when user clicks on UPI app button (GPay/PhonePe/Paytm).
    Uses BOT_TOKEN_QR.
    """
    text = (
        f"💳 <b>New UPI PAYMENT STARTED 🎉</b>\n\n"
        f"👤 Username: <code>{data.username}</code>\n"
        f"📱 Mobile: <code>{data.mobile or 'Not Provided'}</code>\n"
        f"📦 Package: <code>{data.package}</code>\n"
        f"💰 Amount: <code>₹{data.amount}</code>\n"
        f"🏦 Payment Method: <b>{data.method}</b>\n"
        f"🌐 IP: <code>{data.ip}</code>"
    )
    result = await send_telegram(BOT_TOKEN_QR, CHAT_ID, text, parse_mode="HTML")
    return {"success": True, "telegram_response": result}

@app.post("/api/notify/payment-time-ended")
async def notify_payment_time_ended(data: PaymentTimeEnded):
    """
    Send notification when the 3-minute timer expires.
    Uses BOT_TOKEN_QR.
    """
    text = (
        f"⚠️ <b>PAYMENT TIME ENDED</b>\n\n"
        f"👤 Username: <code>{data.username}</code>\n"
        f"📱 Mobile: <code>{data.mobile or 'Not Provided'}</code>\n"
        f"📦 Package: <code>{data.package}</code>\n"
        f"💰 Amount: <code>₹{data.amount}</code>\n"
        f"🏦 Payment Method: <b>{data.method}</b>\n"
        f"🌐 IP: <code>{data.ip}</code>"
    )
    result = await send_telegram(BOT_TOKEN_QR, CHAT_ID, text, parse_mode="HTML")
    return {"success": True, "telegram_response": result}

@app.post("/api/notify/order")
async def notify_order(data: OrderNotification):
    """
    Send notification when user clicks "Get Now" on a package.
    Uses BOT_TOKEN_ORDER.
    """
    text = (
        f"🛒 <b>New Purchase Request</b>\n\n"
        f"👤 Username: <code>{data.username}</code>\n"
        f"📱 Mobile: <code>{data.mobile or 'Not Provided'}</code>\n"
        f"📦 Package: {data.package}\n"
        f"💰 Amount: ₹{data.price}\n"
        f"🌐 IP: {data.ip}"
    )
    result = await send_telegram(BOT_TOKEN_ORDER, CHAT_ID, text, parse_mode="HTML")
    return {"success": True, "telegram_response": result}

# Run with: uvicorn main:app --reload
