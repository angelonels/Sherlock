from app.db.models import DatasetQualityIssue
from app.db.repositories.base import Repository


class DatasetQualityIssuesRepository(Repository[DatasetQualityIssue]):
    model = DatasetQualityIssue

