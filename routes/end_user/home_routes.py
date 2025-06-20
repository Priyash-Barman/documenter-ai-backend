from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from decorators.authenticator import login_required
from utils.logger import logger

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
@login_required("end_user")
async def landing_page(request: Request):
    """Landing page with user info and logout button"""
    try:
        user = request.state.user

        return templates.TemplateResponse("end_user/home.html", {
            "request": request,
            "user": user,
        })

    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        response = RedirectResponse(url="/login")
        response.delete_cookie("access_token")
        return response