"""
Sherlock — Autonomous Data Scientist.

FastAPI application entry point.
"""

import contextlib
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from database import engine, Base
import models
from fastapi import Depends
from routers import auth
from utils.auth import get_current_user
from api.router import api_router

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


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex}")
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
                "details": None,
                "request_id": request_id,
            }
        },
        headers={"X-Request-ID": request_id},
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


app.include_router(auth.router)
app.include_router(api_router)

@app.get("/me")
async def get_my_profile(current_user: models.User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.email}, your token is valid!"}
