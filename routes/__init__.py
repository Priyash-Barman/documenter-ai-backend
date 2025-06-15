from fastapi import FastAPI

from schemas.response_schema import ErrorResponse
from .end_user import user_routes, home_routes
from .admin import (
    manage_user_routes,
    dashboard_routes,
    manage_package_routes,
    manage_app_routes,
    manage_api_doc_routes,
    manage_transaction_routes,
    manage_subscription_routes,
    manage_history_routes,
    manage_log_routes
)


def register_routes(app: FastAPI):
    app.include_router(home_routes.router, prefix="", tags=["Home"], responses=ErrorResponse.get_common_responses())

    # end user routes =========
    app.include_router(user_routes.router, prefix="/api/v1", tags=["Users"], responses=ErrorResponse.get_common_responses())
    # app.include_router(auth_routes.router, prefix="/routes/v1", tags=["Auth"])

    # admin routes ============
    app.include_router(manage_user_routes.router, prefix="/admin", tags=["Manage Users"], responses=ErrorResponse.get_common_responses())
    app.include_router(dashboard_routes.router, prefix="/admin", tags=["Dashboard"], responses=ErrorResponse.get_common_responses())
    app.include_router(manage_package_routes.router, prefix="/admin", tags=["Manage Packages"], responses=ErrorResponse.get_common_responses())
    app.include_router(manage_app_routes.router, prefix="/admin", tags=["Manage Apps"], responses=ErrorResponse.get_common_responses())
    app.include_router(manage_api_doc_routes.router, prefix="/admin", tags=["Manage API Docs"], responses=ErrorResponse.get_common_responses())
    app.include_router(manage_transaction_routes.router, prefix="/admin", tags=["Manage Transactions"], responses=ErrorResponse.get_common_responses())
    app.include_router(manage_subscription_routes.router, prefix="/admin", tags=["Manage Subscriptions"], responses=ErrorResponse.get_common_responses())
    app.include_router(manage_history_routes.router, prefix="/admin", tags=["Manage Histories"], responses=ErrorResponse.get_common_responses())
    app.include_router(manage_log_routes.router, prefix="/admin", tags=["Manage Logs"], responses=ErrorResponse.get_common_responses())