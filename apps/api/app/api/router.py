from fastapi import APIRouter

from app.api.routes import analysis_runs, chats, datasets, health, internal, messages, upload_sessions, users


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(users.router)
api_router.include_router(upload_sessions.router)
api_router.include_router(datasets.router)
api_router.include_router(chats.router)
api_router.include_router(messages.router)
api_router.include_router(analysis_runs.router)
api_router.include_router(internal.router)

