from fastapi import FastAPI

from schemas.response_schema import ErrorResponse
from . import user_routes, home_routes


def register_routes(app: FastAPI):
    app.include_router(user_routes.router, prefix="/api/v1", tags=["Users"], responses=ErrorResponse.get_common_responses())
    app.include_router(home_routes.router, prefix="", tags=["Home"], responses=ErrorResponse.get_common_responses())
    # app.include_router(auth_routes.router, prefix="/routes/v1", tags=["Auth"])
