from app.db.models import ChatMessage
from app.db.repositories.base import Repository


class MessagesRepository(Repository[ChatMessage]):
    model = ChatMessage

