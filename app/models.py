from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean
from datetime import datetime, timezone
from app.database import Base

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True)
    customer_phone = Column(String, index=True)
    
    # Delivery tracking states
    status = Column(String, default="pending") # pending, sent, delivered, read, failed
    message_id = Column(String, index=True, nullable=True) # Used to match incoming webhooks
    
    event_data = Column(JSON)
    retry_count = Column(Integer, default=0)
    provider_used = Column(String) # 'mock' or 'meta'
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
