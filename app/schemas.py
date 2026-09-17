from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum

class EventType(str, Enum):
    REGISTRATION = "registration"
    BOOKING_CREATED = "booking_created"
    PAYMENT_SUCCESS = "payment_success"
    BOOKING_REMINDER = "booking_reminder"
    CANCELLATION = "cancellation"

class NotificationEvent(BaseModel):
    event_type: EventType
    customer_phone: str = Field(..., description="Customer's registered mobile number with country code")
    customer_name: Optional[str] = None
    event_data: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Additional data for the message template (e.g., booking ID, amount)"
    )
