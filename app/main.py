from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
import asyncio
from app.config import settings
from app.schemas import NotificationEvent
from app.database import engine, get_db, Base, SessionLocal
from app import models
from app.engine import NotificationEngine

# Automatically create the database tables when the app starts
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    description="Proof of Concept for automated WhatsApp notifications",
    version="1.0.0"
)

class WebhookPayload(BaseModel):
    message_id: str
    status: str # delivered, read, failed

# --- AUTOMATION BACKGROUND TASKS ---
def auto_retry_task(log_id: int):
    """Simulates an automated Cron/Celery job that retries failed messages."""
    import time
    time.sleep(2) # Wait 2 seconds before retrying
    db = SessionLocal()
    try:
        engine_client = NotificationEngine(db)
        engine_client.retry_failed_message(log_id)
    finally:
        db.close()

async def simulate_meta_webhook_flow(message_id: str, phone: str):
    """Simulates Meta automatically sending webhooks back to our server over time."""
    await asyncio.sleep(1.5)
    db = SessionLocal()
    try:
        if phone.endswith("000"):
            whatsapp_webhook_internal(WebhookPayload(message_id=message_id, status="failed"), db)
        else:
            whatsapp_webhook_internal(WebhookPayload(message_id=message_id, status="delivered"), db)
            await asyncio.sleep(1.5)
            whatsapp_webhook_internal(WebhookPayload(message_id=message_id, status="read"), db)
    finally:
        db.close()

def whatsapp_webhook_internal(payload: WebhookPayload, db: Session):
    """Internal function for webhook processing to allow background tasks to call it."""
    db_log = db.query(models.NotificationLog).filter(models.NotificationLog.message_id == payload.message_id).first()
    if not db_log: return
    
    db_log.status = payload.status
    db.commit()
    
    # AUTOMATIC RETRY ENGINE
    if payload.status == "failed" and db_log.retry_count < 1:
        auto_retry_task(db_log.id)


# --- ROUTES ---
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def read_root():
    """Serve the dashboard HTML page on the root URL."""
    html_path = os.path.join(os.path.dirname(__file__), "..", "static", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

# --- MOCK CORE APPLICATION API ---
class BookingRequest(BaseModel):
    customer_phone: str
    booking_id: str
    whatsapp_opt_in: bool = True

@app.post("/api/v1/bookings")
def create_mock_booking(booking: BookingRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Simulates the actual Cookdin Backend creating a booking.
    When a booking is created, it automatically generates a BOOKING_CREATED event
    and passes it to the Notification Service (Internal Event Bus Simulation).
    """
    # 1. (Simulated) Save booking to core database here...
    
    # 2. Automatically generate the NotificationEvent
    event = NotificationEvent(
        event_type="BOOKING_CREATED",
        customer_phone=booking.customer_phone,
        whatsapp_opt_in=booking.whatsapp_opt_in,
        event_data={"booking_id": booking.booking_id}
    )
    
    # 3. Trigger Notification Engine internally
    engine_client = NotificationEngine(db)
    result = engine_client.process_event(event)
    
    if settings.use_mock_api and result.get("message_id"):
        background_tasks.add_task(simulate_meta_webhook_flow, result["message_id"], event.customer_phone)
        
    return {"status": "success", "message": "Booking created. Notification automatically triggered."}


# --- NOTIFICATION ENGINE INTEGRATION ENDPOINTS ---
@app.post("/api/v1/notify")
def trigger_notification(event: NotificationEvent, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    External API Integration Boundary. 
    Can be used if external microservices need to trigger notifications.
    """
    engine_client = NotificationEngine(db)
    result = engine_client.process_event(event)
    if result["status"] == "failed":
        raise HTTPException(status_code=500, detail=result)
    if settings.use_mock_api and result.get("message_id"):
        background_tasks.add_task(simulate_meta_webhook_flow, result["message_id"], event.customer_phone)
    return result

@app.post("/webhook/whatsapp")
def whatsapp_webhook(payload: WebhookPayload, db: Session = Depends(get_db)):
    """
    Webhook endpoint to automatically receive status updates from Meta.
    """
    whatsapp_webhook_internal(payload, db)
    return {"status": "success"}

@app.get("/api/v1/notifications")
def get_notifications(db: Session = Depends(get_db)):
    """Fetch all notification logs from the database."""
    logs = db.query(models.NotificationLog).all()
    return logs
