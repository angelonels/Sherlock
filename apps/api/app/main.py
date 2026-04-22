import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

from app.api.router import api_router
from app.core.config import get_settings
from app.core.cors import configure_cors
from app.core.errors import configure_error_handlers
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
    )
    app.state.settings = settings
    app.state.logger = configure_logging(settings)

    configure_cors(app, settings)
    configure_error_handlers(app)

    @app.middleware("http")
    async def add_request_id(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get(settings.request_id_header) or f"req_{uuid.uuid4().hex}"
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[settings.request_id_header] = request_id
        return response

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()

