from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status
from typing import Any

def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": message,
            "message": message,
            "detail": message,
        },
    )

def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    details: list[dict[str, Any]] = []
    for err in errors:
        loc = err.get("loc", [])
        field_parts = [str(part) for part in loc if part != "body"]
        field = ".".join(field_parts) if field_parts else None
        details.append(
            {
                "field": field,
                "message": err.get("msg", "Validation error"),
            }
        )
    first = details[0] if details else {"field": None, "message": "Validation error"}
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "field": first.get("field"),
            "message": first.get("message"),
            "details": details,
        },
    )

def generic_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "error": "Internal Server Error"},
    )
