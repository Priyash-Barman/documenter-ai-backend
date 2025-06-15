# routes/manage_log_routes.py
from fastapi import APIRouter, Request, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from services import services
from decorators.catch_error import catch_error

router = APIRouter(prefix="/logs")
templates = Jinja2Templates(directory="templates")

@router.get("/", name="log:list")
@catch_error
async def list_logs(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    type: Optional[str] = Query(None),
    created_by: Optional[str] = Query(None)
):
    filters = {}
    if type and type.lower() != "null":
        filters["type"] = type.lower()
    if created_by and created_by.lower() != "null":
        filters["created_by"] = created_by

    logs, pagination = await services.log_service.get_logs(
        page=page, limit=limit, filters=filters
    )

    return templates.TemplateResponse("admin/logs/list.html", {
        "request": request,
        "logs": logs,
        "type": type if type != "null" else None,
        "created_by": created_by if created_by != "null" else None,
        "pagination": pagination
    })

@router.get("/{log_id}", name="log:detail")
@catch_error
async def log_detail(request: Request, log_id: str):
    log = await services.log_service.get_log_by_id(log_id)
    if not log:
        return RedirectResponse(url="/admin/logs", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("admin/logs/detail.html", {
        "request": request,
        "log": log
    })