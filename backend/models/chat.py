from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from database import Base
import uuid

class ChatSession(Base):
    __tablename__ = "chat_sessions"


    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    
    title = Column(String, default="New Data Analysis") 
    original_filename = Column(String, nullable=False) 
    
    
    physical_table_name = Column(String, unique=True, nullable=False) 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", backref="chat_sessions")
