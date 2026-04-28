from app.db.models import AnalysisRun
from app.db.repositories.base import Repository


class AnalysisRunsRepository(Repository[AnalysisRun]):
    model = AnalysisRun

