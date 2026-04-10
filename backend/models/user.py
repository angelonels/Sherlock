from sqlalchemy import Column, String, DateTime, func
from database import Base
import uuid

class User(Base):
    __tablename__ = "app_users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    clerk_user_id = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, index=True, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
