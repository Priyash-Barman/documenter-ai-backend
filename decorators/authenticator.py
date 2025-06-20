from functools import wraps
from fastapi import HTTPException, Request, status
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer
from services import services

templates = Jinja2Templates(directory="templates")
security = HTTPBearer()


def login_required(*allowed_roles: str):
    """
    Decorator to protect routes with role-based access control
    Supports both web (cookies) and API (Bearer token) authentication

    Usage:
        @login_required("admin", "end_user")  # Multiple allowed roles
        @login_required("admin")              # Single allowed role
        @login_required()                     # Any authenticated user
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            try:
                # Try to get current user
                current_user = await get_current_user(request)
                request.state.user = current_user

                # Check roles if specified
                if allowed_roles and current_user.role not in allowed_roles:
                    if is_api_request(request):
                        return JSONResponse(
                            {"detail": "Forbidden"},
                            status_code=status.HTTP_403_FORBIDDEN
                        )
                    return templates.TemplateResponse(
                        "common/404.html",
                        {"request": request},
                        status_code=status.HTTP_404_NOT_FOUND
                    )

                return await func(request, *args, **kwargs)

            except HTTPException as e:
                if is_api_request(request):
                    return JSONResponse(
                        {"detail": e.detail},
                        status_code=e.status_code
                    )
                return RedirectResponse(
                    url=f"/login?redirect_uri={request.url.path}",
                    status_code=status.HTTP_303_SEE_OTHER
                )

        return wrapper

    return decorator


def is_api_request(request: Request) -> bool:
    """Check if request is an API request"""
    return "application/json" in request.headers.get("accept", "") or \
        request.headers.get("authorization", "").startswith("Bearer ")


async def get_current_user(request: Request):  # Assuming you have a User model
    """
    Get current user from either cookie or Authorization header
    """
    # Try to get token from Authorization header first
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
    else:
        # Fall back to cookie
        token = request.cookies.get("access_token")
        if token and token.startswith("Bearer "):
            token = token[7:]
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

    try:
        payload = services.auth_service.verify_token(token)
        user = await services.user_service.get_user_by_email(payload.get("sub"))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )