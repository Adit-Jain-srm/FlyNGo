"""Core Pydantic data schemas and response envelopes."""

from typing import Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response containing table record counts."""

    status: str = Field(default="healthy", description="Service health status")
    counts: dict[str, int] = Field(description="Record counts across reference and app tables")


class ErrorResponse(BaseModel):
    """Standardized rule error envelope."""

    rule: str
    message: str
    field: str | None = None
    allowed: Any | None = None
