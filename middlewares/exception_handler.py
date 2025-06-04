from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import traceback

from schemas.response_schema import ErrorResponse


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            # Optional: Log stack trace
            traceback.print_exc()
            return JSONResponse(
                status_code=500,
                content=ErrorResponse.set("Internal Server Error"),
            )
