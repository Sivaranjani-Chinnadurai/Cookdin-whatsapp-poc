from sqlalchemy.orm import Session
from app.schemas import NotificationEvent
from app.models import NotificationLog
from app.providers import get_whatsapp_provider

class NotificationEngine:
    """
    Core engine handling validation, opt-ins, template mapping, logging, and dispatching.
    Separated from the Provider logic.
    """
    def __init__(self, db: Session):
        self.db = db
        self.provider = get_whatsapp_provider()
        self.provider_name = "mock" if self.provider.__class__.__name__ == "MockWhatsAppProvider" else "meta"

    def process_event(self, event: NotificationEvent):
        # 1. Opt-in Check
        if not event.whatsapp_opt_in:
            return {"status": "skipped", "message": f"Customer {event.customer_id} has not opted in to WhatsApp."}

        # 2. Map Event to Template
        template_map = {
            "REGISTRATION": "cookdin_welcome",
            "BOOKING_CREATED": "cookdin_booking_created",
            "BOOKING_CONFIRMED": "cookdin_booking_confirmed",
            "PAYMENT_SUCCESS": "cookdin_payment_success",
            "PAYMENT_FAILED": "cookdin_payment_failed",
            "BOOKING_REMINDER": "cookdin_reminder",
            "BOOKING_CANCELLED": "cookdin_cancelled",
            "REFUND_PROCESSED": "cookdin_refund",
            "BOOKING_COMPLETED": "cookdin_completed"
        }
        template_name = template_map.get(event.event_type.value, "hello_world")
        
        # 3. Dynamic Variables Extraction
        components = []
        if event.event_type.value in ["BOOKING_CREATED", "BOOKING_CONFIRMED", "BOOKING_CANCELLED", "BOOKING_COMPLETED"]:
            booking_id = event.event_data.get("booking_id", "UNKNOWN")
            components = [{"type": "body", "parameters": [{"type": "text", "text": str(booking_id)}]}]
        elif event.event_type.value in ["PAYMENT_SUCCESS", "PAYMENT_FAILED", "REFUND_PROCESSED"]:
            amount = event.event_data.get("amount", "0")
            components = [{"type": "body", "parameters": [{"type": "text", "text": str(amount)}]}]

        # 4. Log Pending Status to Database
        db_log = NotificationLog(
            event_type=event.event_type.value,
            customer_phone=event.customer_phone,
            status="pending",
            event_data=event.event_data,
            provider_used=self.provider_name
        )
        self.db.add(db_log)
        self.db.commit()
        self.db.refresh(db_log)

        # 5. Dispatch via Provider
        return self._dispatch_and_update(db_log, template_name, components)
        
    def retry_failed_message(self, log_id: int):
        """Simulate basic retry handling."""
        db_log = self.db.query(NotificationLog).filter(NotificationLog.id == log_id, NotificationLog.status == "failed").first()
        if not db_log:
            return {"status": "error", "message": "Log not found or not in failed state."}
            
        db_log.retry_count += 1
        db_log.status = "pending"
        self.db.commit()
        
        # For POC retry, we reconstruct template name loosely
        template_name = f"cookdin_{db_log.event_type.lower()}"
        
        return self._dispatch_and_update(db_log, template_name, components=[])

    def _dispatch_and_update(self, db_log, template_name, components):
        success, result = self.provider.send_template_message(
            recipient_phone=db_log.customer_phone,
            template_name=template_name,
            components=components
        )

        if success:
            db_log.status = "sent"
            # Extract Meta Message ID for Webhook tracking
            try:
                db_log.message_id = result.get("messages", [])[0].get("id")
            except Exception:
                pass
            self.db.commit()
            return {"status": "success", "message": "Dispatched to provider", "log_id": db_log.id, "message_id": db_log.message_id}
        else:
            db_log.status = "failed"
            self.db.commit()
            return {"status": "failed", "message": "Provider rejected message", "log_id": db_log.id, "error": result}
