from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(100), unique=True, nullable=False, index=True)
    hostname = Column(String(100))
    ip_address = Column(String(15))
    platform = Column(String(50))
    version = Column(String(20))
    is_online = Column(Boolean, default=False)
    device_count = Column(Integer, default=0)
    online_count = Column(Integer, default=0)
    last_heartbeat = Column(DateTime)
    last_scan = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
