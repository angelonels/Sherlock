"""
Sherlock — Autonomous Data Scientist.

FastAPI application entry point.
"""

import contextlib
from fastapi import FastAPI
from database import engine, Base
from models import user, chat

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="Sherlock",
    description="Autonomous Data Scientist",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "sherlock",
        "status": "operational",
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    """Health-check endpoint."""
    return {"status": "ok"}
