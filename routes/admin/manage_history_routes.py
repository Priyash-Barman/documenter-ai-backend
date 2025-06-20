# routes/manage_history_routes.py
from fastapi import APIRouter, Request, Query, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from decorators.authenticator import login_required
from services import services
from decorators.catch_error import catch_error

router = APIRouter(prefix="/histories")
templates = Jinja2Templates(directory="templates")

@router.get("/", name="history:list")
@catch_error
@login_required("admin")
async def list_histories(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    req_from: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    app_id: Optional[str] = Query(None)
):
    filters = {}
    if req_from and req_from.lower() != "null":
        filters["req_from"] = req_from.lower()
    if user_id and user_id.lower() != "null":
        filters["user_id"] = user_id
    if app_id and app_id.lower() != "null":
        filters["app_id"] = app_id

    histories, pagination = await services.history_service.get_histories(
        page=page, limit=limit, filters=filters
    )

    return templates.TemplateResponse("admin/histories/list.html", {
        "request": request,
        "histories": histories,
        "req_from": req_from if req_from != "null" else None,
        "user_id": user_id if user_id != "null" else None,
        "app_id": app_id if app_id != "null" else None,
        "pagination": pagination
    })

@router.get("/{history_id}", name="history:detail")
@catch_error
@login_required("admin")
async def history_detail(request: Request, history_id: str):
    history = await services.history_service.get_history_by_id(history_id)
    if not history:
        return RedirectResponse(url="/admin/histories", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("admin/histories/detail.html", {
        "request": request,
        "history": history
    })