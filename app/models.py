from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime, timezone
from app.database import Base

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True)
    customer_phone = Column(String, index=True)
    status = Column(String, default="pending") # Can be: pending, sent, failed
    event_data = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
