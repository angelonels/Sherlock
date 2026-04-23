from fastapi import APIRouter

from app.schemas.common import DataEnvelope


router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=DataEnvelope[dict[str, str]])
async def read_health() -> dict[str, dict[str, str]]:
    return {"data": {"status": "ok"}}

