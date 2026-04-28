from app.db.models import QueryAttempt
from app.db.repositories.base import Repository


class QueryAttemptsRepository(Repository[QueryAttempt]):
    model = QueryAttempt

