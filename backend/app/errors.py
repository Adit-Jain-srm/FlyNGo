"""Domain exceptions and API error responses for FlyNGo."""

from typing import Any
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


HTTP_422_UNPROCESSABLE = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)


class RuleViolationException(Exception):
    """Raised when a business rule (R1-R9) is violated."""

    def __init__(
        self,
        rule: str,
        message: str,
        field: str | None = None,
        allowed: Any | None = None,
        status_code: int = HTTP_422_UNPROCESSABLE,
    ):
        self.rule = rule
        self.field = field
        self.message = message
        self.allowed = allowed
        self.status_code = status_code
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "rule": self.rule,
            "message": self.message,
        }
        if self.field is not None:
            result["field"] = self.field
        if self.allowed is not None:
            result["allowed"] = self.allowed
        return result


RuleRefusalException = RuleViolationException


class ConflictException(RuleViolationException):
    """Raised on state conflicts (e.g. double booking, offer not open)."""

    def __init__(
        self,
        message: str,
        rule: str = "CONFLICT",
        field: str | None = None,
        allowed: Any | None = None,
    ):
        super().__init__(
            rule=rule,
            message=message,
            field=field,
            allowed=allowed,
            status_code=status.HTTP_409_CONFLICT,
        )


class NotFoundException(Exception):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str = "Resource not found"):
        self.message = message
        self.status_code = status.HTTP_404_NOT_FOUND
        super().__init__(message)


def register_exception_handlers(app: FastAPI) -> None:
    """Register uniform error handlers for all exceptions."""

    @app.exception_handler(RuleViolationException)
    async def rule_violation_handler(_: Request, exc: RuleViolationException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )

    @app.exception_handler(NotFoundException)
    async def not_found_handler(_: Request, exc: NotFoundException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": exc.message},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        first_err = exc.errors()[0] if exc.errors() else {}
        loc = first_err.get("loc", [])
        field_name = str(loc[-1]) if loc else None
        msg = first_err.get("msg", "Invalid input")
        return JSONResponse(
            status_code=HTTP_422_UNPROCESSABLE,
            content={
                "rule": "INPUT",
                "field": field_name,
                "message": msg,
                "details": exc.errors(),
            },
        )
