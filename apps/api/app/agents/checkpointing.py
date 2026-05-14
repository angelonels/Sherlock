from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

from app.core.config import Settings


def checkpoint_connection_string(database_url: str) -> str:
    if database_url.startswith("postgresql+psycopg://"):
        return database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    return database_url


@asynccontextmanager
async def open_checkpointer(settings: Settings) -> AsyncIterator[AsyncPostgresSaver]:
    async with AsyncPostgresSaver.from_conn_string(
        checkpoint_connection_string(settings.database_url),
        serde=JsonPlusSerializer(),
    ) as checkpointer:
        yield checkpointer


async def setup_checkpointer(settings: Settings) -> None:
    async with open_checkpointer(settings) as checkpointer:
        await checkpointer.setup()
