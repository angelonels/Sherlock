from sqlalchemy import Column, String, DateTime, func
from database import Base
import uuid

class User(Base):
    __tablename__ = "users"

    # Using UUIDs is safer for distributed systems than auto-incrementing integers
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
