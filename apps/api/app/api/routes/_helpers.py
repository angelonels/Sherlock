from fastapi import status

from app.core.errors import ApiError


def not_implemented(resource: str) -> None:
    raise ApiError(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        code="NOT_IMPLEMENTED",
        message=f"{resource} is not implemented yet.",
    )


def not_found(resource: str) -> None:
    raise ApiError(
        status_code=status.HTTP_404_NOT_FOUND,
        code="NOT_FOUND",
        message=f"{resource} not found.",
    )

