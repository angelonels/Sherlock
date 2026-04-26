from app.db.models import DatasetColumn
from app.db.repositories.base import Repository


class DatasetColumnsRepository(Repository[DatasetColumn]):
    model = DatasetColumn

