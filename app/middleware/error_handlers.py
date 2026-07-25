import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.shortener import (
    InvalidShortCodeError,
    InvalidUrlError,
    ShortCodeCollisionError,
    ShortCodeNotFoundError,
    ShortenerError,
)

logger = logging.getLogger(__name__)


def _error_response(
    *,
    status_code: int,
    error: str,
    message: str,
    details: list[dict[str, object]] | None = None,
) -> JSONResponse:
    payload: dict[str, object] = {"error": error, "message": message}
    if details:
        payload["details"] = details
    return JSONResponse(status_code=status_code, content=payload)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(InvalidUrlError)
    async def handle_invalid_url(_: Request, exc: InvalidUrlError) -> JSONResponse:
        return _error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="invalid_url",
            message=str(exc),
        )

    @app.exception_handler(InvalidShortCodeError)
    async def handle_invalid_short_code(_: Request, exc: InvalidShortCodeError) -> JSONResponse:
        return _error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="invalid_short_code",
            message=str(exc),
        )

    @app.exception_handler(ShortCodeNotFoundError)
    async def handle_short_code_not_found(
        _: Request, exc: ShortCodeNotFoundError
    ) -> JSONResponse:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            error="short_code_not_found",
            message=str(exc),
        )

    @app.exception_handler(ShortCodeCollisionError)
    async def handle_short_code_collision(
        _: Request, exc: ShortCodeCollisionError
    ) -> JSONResponse:
        logger.error(f"Short code collision: {exc}")
        return _error_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error="service_unavailable",
            message="Could not generate a unique short code at this time.",
        )

    @app.exception_handler(ShortenerError)
    async def handle_general_shortener_error(
        _: Request, exc: ShortenerError
    ) -> JSONResponse:
        logger.error(f"Internal shortener error: {exc}")
        return _error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="internal_error",
            message="An internal domain error occurred.",
        )

    @app.exception_handler(SQLAlchemyError)
    async def handle_sqlalchemy_error(_: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.error(f"Database error: {exc}")
        return _error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="database_error",
            message="An internal database error occurred.",
        )

    @app.exception_handler(Exception)
    async def handle_general_exception(_: Request, exc: Exception) -> JSONResponse:
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        return _error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="internal_error",
            message="An unexpected error occurred.",
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            {"field": ".".join(map(str, error["loc"])), "message": error["msg"]}
            for error in exc.errors()
        ]
        return _error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error="validation_error",
            message="Request validation failed.",
            details=details,
        )
