import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings
from app.utils.responses import error_response

logger = logging.getLogger("ccms.errors")

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_error(_: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content=error_response(str(exc.detail), [{"message": str(exc.detail), "code": "http_error"}]), headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        errors = [{"field": ".".join(str(v) for v in item["loc"][1:]) or None, "message": item["msg"], "code": item["type"]} for item in exc.errors()]
        return JSONResponse(status_code=422, content=error_response("Request validation failed", errors))

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError):
        logger.exception("Database error request_id=%s", getattr(request.state, "request_id", None))
        message = str(exc) if settings.DEBUG else "A database error occurred"
        return JSONResponse(status_code=500, content=error_response(message, [{"message": message, "code": "database_error"}]))

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logger.exception("Unhandled server error request_id=%s", getattr(request.state, "request_id", None))
        message = str(exc) if settings.DEBUG else "An unexpected server error occurred"
        return JSONResponse(status_code=500, content=error_response(message, [{"message": message, "code": "server_error"}]))
