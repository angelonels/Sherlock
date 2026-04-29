import pytest

from app.core.database import get_db_session


@pytest.mark.asyncio
async def test_db_session_dependency_can_be_initialized():
    async for session in get_db_session():
        assert session is not None
        break

