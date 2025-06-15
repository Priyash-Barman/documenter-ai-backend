# routes/manage_app_routes.py
from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import status
from typing import Optional

from services import services
from schemas.app_schema import AppCreate, AppUpdate
from decorators.catch_error import catch_error

router = APIRouter(prefix="/apps")
templates = Jinja2Templates(directory="templates")

@router.get("/", name="app:list")
@catch_error
async def list_apps(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    is_active: Optional[str] = Query(None),
    owner_id: Optional[str] = Query(None)
):
    filters = {}
    if is_active and is_active.lower() != "null":
        filters["is_active"] = is_active.lower() == "true"
    if owner_id and owner_id.lower() != "null":
        filters["owner_id"] = owner_id

    apps, pagination = await services.app_service.get_apps(
        page=page, limit=limit, search=search, sort=sort, filters=filters
    )

    return templates.TemplateResponse("admin/apps/list.html", {
        "request": request,
        "apps": apps,
        "search": search,
        "sort": sort,
        "is_active": is_active if is_active != "null" else None,
        "owner_id": owner_id if owner_id != "null" else None,
        "pagination": pagination
    })

@router.get("/create", name="app:create_form")
@catch_error
async def create_app_form(request: Request):
    return templates.TemplateResponse("admin/apps/form.html", {
        "request": request,
        "app": None,
        "form_action": "/apps/create",
        "form_method": "POST"
    })

@router.post("/create", name="app:create")
@catch_error
async def create_app(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    owner_id: str = Form(...),
    is_active: bool = Form(False)
):
    app_data = AppCreate(
        name=name,
        description=description,
        owner_id=owner_id,
        is_active=is_active
    )
    try:
        await services.app_service.create_new_app(app_data)
    except ValueError:
        return RedirectResponse(url="/admin/apps/create", status_code=status.HTTP_302_FOUND)

    return RedirectResponse(url="/admin/apps", status_code=status.HTTP_302_FOUND)

@router.get("/{app_id}/edit", name="app:edit_form")
@catch_error
async def edit_app_form(request: Request, app_id: str):
    app = await services.app_service.get_app_by_id(app_id)
    if not app:
        return RedirectResponse(url="/admin/apps", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("admin/apps/form.html", {
        "request": request,
        "app": app,
        "form_action": f"/apps/{app_id}/edit",
        "form_method": "POST"
    })

@router.post("/{app_id}/edit", name="app:update")
@catch_error
async def update_app(
    request: Request,
    app_id: str,
    name: str = Form(...),
    description: str = Form(...),
    is_active: bool = Form(False)
):
    app_data = AppUpdate(
        name=name,
        description=description,
        is_active=is_active
    )
    await services.app_service.update_app_details(app_id, app_data)
    return RedirectResponse(url="/admin/apps", status_code=status.HTTP_302_FOUND)

@router.get("/{app_id}/delete", name="app:delete")
@catch_error
async def delete_app(app_id: str):
    await services.app_service.remove_app(app_id)
    return RedirectResponse(url="/admin/apps", status_code=status.HTTP_302_FOUND)

@router.get("/{app_id}/toggle", name="app:toggle_status")
@catch_error
async def toggle_app_status(app_id: str):
    app = await services.app_service.get_app_by_id(app_id)
    if app:
        await services.app_service.change_app_status(app_id, not app.is_active)
    return RedirectResponse(url="/admin/apps", status_code=status.HTTP_302_FOUND)