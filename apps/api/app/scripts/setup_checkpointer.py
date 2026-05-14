from __future__ import annotations

import asyncio

from app.agents.checkpointing import setup_checkpointer
from app.core.config import get_settings


async def main() -> None:
    await setup_checkpointer(get_settings())


if __name__ == "__main__":
    asyncio.run(main())
