import uuid

from app.db.models import ChatSession
from app.services.title_service import TitleService


def test_title_generated_from_first_question_and_manual_title_is_not_overwritten() -> None:
    service = TitleService()

    assert service.generate("How many rows are there in revenue data?") == "How many rows are there in revenue data"


async def test_title_service_does_not_overwrite_manual_title() -> None:
    chat = ChatSession(id=uuid.uuid4(), user_id=uuid.uuid4(), dataset_id=uuid.uuid4(), title="Manual title")

    await TitleService().generate_after_success(session=NoopSession(), chat=chat, first_question="Total revenue")

    assert chat.title == "Manual title"


class NoopSession:
    async def flush(self) -> None:
        return None
