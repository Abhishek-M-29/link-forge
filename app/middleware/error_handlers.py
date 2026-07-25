import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError



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
