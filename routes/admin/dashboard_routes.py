from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from decorators.authenticator import login_required
from decorators.catch_error import catch_error

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("")
@catch_error
@login_required("admin")
async def dashboard(request: Request):
    print(request.state.user)
    return templates.TemplateResponse("admin/dashboard/index.html", {"request":request})
