from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base

class DeviceCorrection(Base):
    __tablename__ = "device_corrections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mac_address = Column(String(17), nullable=False, index=True)
    field_name = Column(String(50), nullable=False)
    old_value = Column(String(200))
    new_value = Column(String(200), nullable=False)
    corrected_by = Column(String(100), default="user")
    reason = Column(Text)
    created_at = Column(DateTime, default=func.now())
