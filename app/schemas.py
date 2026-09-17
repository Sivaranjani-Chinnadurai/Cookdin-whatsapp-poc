from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum

class EventType(str, Enum):
    REGISTRATION = "REGISTRATION"
    BOOKING_CREATED = "BOOKING_CREATED"
    BOOKING_CONFIRMED = "BOOKING_CONFIRMED"
    PAYMENT_SUCCESS = "PAYMENT_SUCCESS"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    BOOKING_REMINDER = "BOOKING_REMINDER"
    BOOKING_CANCELLED = "BOOKING_CANCELLED"
    REFUND_PROCESSED = "REFUND_PROCESSED"
    BOOKING_COMPLETED = "BOOKING_COMPLETED"

class NotificationEvent(BaseModel):
    event_type: EventType
    customer_phone: str = Field(..., description="Customer's registered mobile number with country code")
    customer_id: str = Field(default="UNKNOWN", description="Customer ID for database lookup")
    
    # In production, this would be queried from the Customer DB. 
    # Passed here to simulate the opt-in check.
    whatsapp_opt_in: bool = Field(default=True, description="Whether the user has opted in to WhatsApp messages")
    
    event_data: Dict[str, Any] = Field(default_factory=dict)
