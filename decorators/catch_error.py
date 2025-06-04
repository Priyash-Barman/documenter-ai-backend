# utils/decorators.py
import traceback

from fastapi import status
from functools import wraps
from typing import Callable, Any, Coroutine

from starlette.responses import JSONResponse

from schemas.response_schema import ErrorResponse

def catch_error(func: Callable[..., Coroutine[Any, Any, Any]]):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception:
            # Optional: Log stack trace
            traceback.print_exc()
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=ErrorResponse.set("Internal Server Error"),
            )
    return wrapper