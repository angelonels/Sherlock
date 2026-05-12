import asyncio
import logging

from app.workers.analysis_worker import AnalysisWorker
from app.workers.dataset_worker import DatasetWorker
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.maintenance_service import MaintenanceService


async def run_worker() -> None:
    logger = logging.getLogger("sherlock.worker")
    logger.info("Sherlock worker started")
    dataset_worker = DatasetWorker()
    analysis_worker = AnalysisWorker()
    maintenance = MaintenanceService()
    settings = get_settings()
    while True:
        await dataset_worker.run_once()
        await analysis_worker.run_once()
        async with SessionLocal() as session:
            await maintenance.cleanup_expired_upload_sessions(session, settings)
            await maintenance.cleanup_ingested_upload_files(session, settings)
            await maintenance.fail_stuck_analysis_runs(session)
        await asyncio.sleep(30)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
