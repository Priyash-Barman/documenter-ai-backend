from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer

from services import services
from schemas.response_schema import ErrorResponse
from utils.logger import logger

router = APIRouter()
templates = Jinja2Templates(directory="templates")
security = HTTPBearer()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, redirect_uri: str = "/"):
    """Render login page with email input form"""
    return templates.TemplateResponse("auth/login.html", {
        "request": request,
        "redirect_uri": redirect_uri,
        "step": "email"
    })


@router.post("/send-otp", response_class=HTMLResponse)
async def send_otp(
        request: Request,
        email: str = Form(...),
        redirect_uri: str = Form("/")
):
    """Handle OTP sending request"""
    try:
        # Check if resend is allowed
        can_resend, remaining = await services.auth_service.can_resend_otp(email)
        if not can_resend:
            return templates.TemplateResponse("auth/login.html", {
                "request": request,
                "redirect_uri": redirect_uri,
                "email": email,
                "step": "otp",
                "resend_cooldown": remaining,
                "error": f"Please wait {remaining} seconds before requesting a new OTP"
            })

        success = await services.auth_service.send_login_otp(email)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    message="Failed to send OTP",
                    data={"email": email}
                ).dict()
            )

        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "redirect_uri": redirect_uri,
            "email": email,
            "step": "otp",
            "resend_cooldown": 30  # 30 seconds
        })

    except Exception as e:
        logger.error(f"OTP send failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                message="Internal server error",
                data={"email": email}
            ).dict()
        )


@router.post("/verify-otp", response_class=HTMLResponse)
async def verify_otp(
        request: Request,
        email: str = Form(...),
        otp: str = Form(...),
        redirect_uri: str = Form("/")
):
    """Handle OTP verification"""
    try:
        verified, user = await services.auth_service.verify_otp(email, otp)

        if not verified:
            return templates.TemplateResponse("auth/login.html", {
                "request": request,
                "redirect_uri": redirect_uri,
                "email": email,
                "step": "otp",
                "error": "Invalid or expired OTP"
            })

        if user:
            token = await services.auth_service.generate_auth_token(email)
            # Check if user is admin and redirect accordingly
            is_admin = user.role == "admin"
            final_redirect = "/admin" if is_admin else (redirect_uri or "/")
            return await handle_successful_login(final_redirect, token)

        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "redirect_uri": redirect_uri,
            "email": email,
            "step": "name"
        })

    except Exception as e:
        logger.error(f"OTP verification failed: {str(e)}")
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "redirect_uri": redirect_uri,
            "email": email,
            "step": "otp",
            "error": "Verification failed"
        })


@router.post("/complete-registration", response_class=HTMLResponse)
async def complete_registration(
        request: Request,
        email: str = Form(...),
        full_name: str = Form(...),
        redirect_uri: str = Form("/")
):
    """Handle new user registration"""
    try:
        user = await services.auth_service.create_new_user(email, full_name)
        token = await services.auth_service.generate_auth_token(email)
        return await handle_successful_login(redirect_uri or "/", token)

    except ValueError as e:
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "redirect_uri": redirect_uri,
            "email": email,
            "step": "name",
            "error": str(e)
        })

    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "redirect_uri": redirect_uri,
            "email": email,
            "step": "name",
            "error": "Registration failed"
        })


@router.get("/logout")
async def logout():
    """Handle user logout"""
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=True,
        samesite="lax"
    )
    return response


async def handle_successful_login(redirect_uri: str, token: str):
    """
    Handle post-login redirect with token
    - Verifies token and gets user data
    - Redirects to /admin for admin users
    - Redirects to / for regular users
    - Handles app deep links
    """
    try:
        # Verify token and get user email
        payload = services.auth_service.verify_token(token)
        email = payload.get("sub")

        # Get user data from database
        user = await services.user_service.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        # Determine redirect URL based on role
        is_admin = user.role == "admin"
        if redirect_uri and redirect_uri.startswith("yourapp://"):
            final_redirect = f"{redirect_uri}?access_token={token}"
        else:
            final_redirect = "/admin" if is_admin else (redirect_uri or "/")

        # Create response with cookie
        response = RedirectResponse(
            url=final_redirect,
            status_code=status.HTTP_303_SEE_OTHER
        )
        response.set_cookie(
            key="access_token",
            value=f"Bearer {token}",
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=3600  # 1 hour expiration
        )
        return response

    except Exception as e:
        logger.error(f"Login handling failed: {str(e)}")
        # Fallback to default redirect if something goes wrong
        response = RedirectResponse(
            url=redirect_uri or "/",
            status_code=status.HTTP_303_SEE_OTHER
        )
        response.delete_cookie("access_token")
        return response