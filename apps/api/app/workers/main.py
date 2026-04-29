import asyncio
import logging

from app.workers.analysis_worker import AnalysisWorker
from app.workers.dataset_worker import DatasetWorker


async def run_worker() -> None:
    logger = logging.getLogger("sherlock.worker")
    logger.info("Sherlock worker started")
    dataset_worker = DatasetWorker()
    analysis_worker = AnalysisWorker()
    while True:
        await dataset_worker.run_once()
        await analysis_worker.run_once()
        await asyncio.sleep(30)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
