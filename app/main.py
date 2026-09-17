from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import os
from app.config import settings
from app.schemas import NotificationEvent
from app.database import engine, get_db, Base
from app import models
from app.whatsapp import WhatsAppClient

# Automatically create the database tables when the app starts
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    description="Proof of Concept for automated WhatsApp notifications",
    version="1.0.0"
)

# Initialize WhatsApp client
whatsapp_client = WhatsAppClient()

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def read_root():
    """Serve the dashboard HTML page on the root URL."""
    html_path = os.path.join(os.path.dirname(__file__), "..", "static", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/v1/notify")
def trigger_notification(event: NotificationEvent, db: Session = Depends(get_db)):
    """
    Endpoint to receive application events, map them to templates, and send WhatsApp messages.
    """
    db_log = models.NotificationLog(
        event_type=event.event_type.value,
        customer_phone=event.customer_phone,
        status="pending",
        event_data=event.event_data
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    
    # Dynamic Template Mapping
    template_name = "hello_world"
    components = []
    
    if event.event_type.value == "booking_created":
        template_name = "cookdin_booking_confirmed"
        booking_id = event.event_data.get("booking_id", "UNKNOWN_ID")
        amount = event.event_data.get("amount", "0")
        components = [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": str(booking_id)},
                    {"type": "text", "text": str(amount)}
                ]
            }
        ]
    elif event.event_type.value == "registration":
        template_name = "cookdin_welcome"
        name = event.customer_name or "Valued Customer"
        components = [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": name}
                ]
            }
        ]
    
    # Call the WhatsApp API (Will hit our local simulator)
    success, result = whatsapp_client.send_template_message(
        recipient_phone=event.customer_phone,
        template_name=template_name,
        components=components
    )
    
    if success:
        db_log.status = "sent"
        db.commit()
        return {
            "status": "success",
            "message": f"WhatsApp message processed successfully for event: {event.event_type.value}",
            "log_id": db_log.id,
            "api_response": result
        }
    else:
        db_log.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to send WhatsApp message. API Error: {result}"
        )

@app.get("/api/v1/notifications")
def get_notifications(db: Session = Depends(get_db)):
    """
    Fetch all notification logs from the database.
    """
    logs = db.query(models.NotificationLog).all()
    return logs

# =====================================================================
# META API SIMULATOR
# =====================================================================
@app.post("/mock-meta/messages", include_in_schema=False)
async def mock_meta_api(request: Request):
    """
    Simulates the real Meta WhatsApp Cloud API.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {settings.whatsapp_api_token}":
        raise HTTPException(
            status_code=401, 
            detail={"error": {"message": "Invalid OAuth access token."}}
        )
        
    payload = await request.json()
    template_data = payload.get("template", {})
    
    return {
        "messaging_product": "whatsapp",
        "contacts": [{"input": payload.get("to"), "wa_id": payload.get("to")}],
        "messages": [{"id": f"wamid.mock_{template_data.get('name')}_123"}],
        "mock_debug_received_template": template_data 
    }
