"""
Sherlock — Autonomous Data Scientist.

FastAPI application entry point.
"""

import contextlib
from fastapi import FastAPI
from database import engine, Base
from models import user, chat
from fastapi import Depends
from routers import auth
from utils.auth import get_current_user

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


from routers import chat as chat_router
app.include_router(auth.router)
app.include_router(chat_router.router)

@app.get("/me")
async def get_my_profile(current_user: user.User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.email}, your token is valid!"}
