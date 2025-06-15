from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from decorators.catch_error import catch_error

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("")
@catch_error
async def dashboard(request: Request):
    return templates.TemplateResponse("admin/dashboard/index.html", {"request":request})
