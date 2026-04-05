# Expose the Base and our models here so Alembic and our database schema registry
# can easily discover them all at once during migrations.
from database import Base
from .user import User
from .chat import ChatSession

__all__ = ["Base", "User", "ChatSession"]
