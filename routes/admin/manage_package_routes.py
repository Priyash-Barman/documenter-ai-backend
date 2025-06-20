# routes/manage_package_routes.py
from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import status
from typing import Optional

from decorators.authenticator import login_required
from services import services
from schemas.package_schema import PackageCreate, PackageUpdate
from decorators.catch_error import catch_error

router = APIRouter(prefix="/packages")
templates = Jinja2Templates(directory="templates")

@router.get("/", name="package:list")
@catch_error
@login_required("admin")
async def list_packages(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    is_active: Optional[str] = Query(None),
    type: Optional[str] = Query(None)
):
    """
    Render list of packages with pagination, filter, sort
    """
    filters = {}

    if is_active and is_active.lower() != "null":
        filters["is_active"] = is_active.lower() == "true"

    if type and type.lower() != "null":
        filters["type"] = type.lower()

    packages, pagination = await services.package_service.get_packages(
        page=page, limit=limit, search=search, sort=sort, filters=filters
    )

    return templates.TemplateResponse("admin/packages/list.html", {
        "request": request,
        "packages": packages,
        "search": search,
        "sort": sort,
        "is_active": is_active if is_active != "null" else None,
        "type": type if type != "null" else None,
        "pagination": pagination
    })

@router.get("/create", name="package:create_form")
@catch_error
@login_required("admin")
async def create_package_form(request: Request):
    return templates.TemplateResponse("admin/packages/form.html", {
        "request": request,
        "package": None,
        "form_action": "/packages/create",
        "form_method": "POST"
    })

@router.post("/create", name="package:create")
@catch_error
@login_required("admin")
async def create_package(
    request: Request,
    name: str = Form(...),
    stripe_price_id: str = Form(...),
    type: str = Form(...),
    is_active: bool = Form(False)
):
    package_data = PackageCreate(
        name=name,
        stripe_price_id=stripe_price_id,
        type=type,
        is_active=is_active
    )
    try:
        await services.package_service.create_new_package(package_data)
    except ValueError:
        return RedirectResponse(url="/admin/packages/create", status_code=status.HTTP_302_FOUND)

    return RedirectResponse(url="/admin/packages", status_code=status.HTTP_302_FOUND)

@router.get("/{package_id}/edit", name="package:edit_form")
@catch_error
@login_required("admin")
async def edit_package_form(request: Request, package_id: str):
    package = await services.package_service.get_package_by_id(package_id)
    if not package:
        return RedirectResponse(url="/admin/packages", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("admin/packages/form.html", {
        "request": request,
        "package": package,
        "form_action": f"/packages/{package_id}/edit",
        "form_method": "POST"
    })

@router.post("/{package_id}/edit", name="package:update")
@catch_error
@login_required("admin")
async def update_package(
    request: Request,
    package_id: str,
    name: str = Form(...),
    stripe_price_id: str = Form(...),
    type: str = Form(...),
    is_active: bool = Form(False)
):
    package_data = PackageUpdate(
        name=name,
        stripe_price_id=stripe_price_id,
        type=type,
        is_active=is_active
    )
    await services.package_service.update_package_details(package_id, package_data)
    return RedirectResponse(url="/admin/packages", status_code=status.HTTP_302_FOUND)

@router.get("/{package_id}/delete", name="package:delete")
@catch_error
@login_required("admin")
async def delete_package(request: Request, package_id: str):
    await services.package_service.remove_package(package_id)
    return RedirectResponse(url="/admin/packages", status_code=status.HTTP_302_FOUND)

@router.get("/{package_id}/toggle", name="package:toggle_status")
@catch_error
@login_required("admin")
async def toggle_package_status(request: Request, package_id: str):
    package = await services.package_service.get_package_by_id(package_id)
    if package:
        await services.package_service.change_package_status(package_id, not package.is_active)
    return RedirectResponse(url="/admin/packages", status_code=status.HTTP_302_FOUND)