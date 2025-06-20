from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import status
from typing import Optional

from decorators.authenticator import login_required
from services import services
from schemas.user_schema import UserCreate, UserUpdate, UserRole
from decorators.catch_error import catch_error

router = APIRouter(prefix="/users")
templates = Jinja2Templates(directory="templates")


@router.get("/", name="user:list")
@catch_error
@login_required("admin")
async def list_users(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    is_active: Optional[str] = Query(None),
    role: Optional[str] = Query(None)
):
    """
    Render list of users with pagination, filter, sort
    """
    filters = {}

    if is_active and is_active.lower() != "null":
        filters["is_active"] = is_active.lower() == "true"

    if role and role.lower() != "null":
        filters["role"] = role.lower()

    users, pagination = await services.user_service.get_users(
        page=page, limit=limit, search=search, sort=sort, filters=filters
    )

    return templates.TemplateResponse("admin/users/list.html", {
        "request": request,
        "users": users,
        "search": search,
        "sort": sort,
        "is_active": is_active if is_active != "null" else None,
        "role": role if role != "null" else None,
        "pagination": pagination
    })


@router.get("/create", name="user:create_form")
@catch_error
@login_required("admin")
async def create_user_form(request: Request):
    return templates.TemplateResponse("admin/users/form.html", {
        "request": request,
        "user": None,
        "form_action": "/users/create",
        "form_method": "POST"
    })


@router.post("/create", name="user:create")
@catch_error
@login_required("admin")
async def create_user(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
):
    user_data = UserCreate(full_name=full_name, email=email, role=UserRole.ADMIN)
    try:
        await services.user_service.create_new_user(user_data)
    except ValueError:
        # Optionally flash message or handle via toastr
        return RedirectResponse(url="/admin/users/create", status_code=status.HTTP_302_FOUND)

    return RedirectResponse(url="/admin/users", status_code=status.HTTP_302_FOUND)


@router.get("/{user_id}/edit", name="user:edit_form")
@catch_error
@login_required("admin")
async def edit_user_form(request: Request, user_id: str):
    user = await services.user_service.get_user_by_id(user_id)
    if not user:
        return RedirectResponse(url="/admin/users", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("admin/users/form.html", {
        "request": request,
        "user": user,
        "form_action": f"/users/{user_id}/edit",
        "form_method": "POST"
    })


@router.post("/{user_id}/edit", name="user:update")
@catch_error
@login_required("admin")
async def update_user(
    request: Request,
    user_id: str,
    full_name: str = Form(...),
    email: str = Form(...),
):
    user_data = UserUpdate(full_name=full_name, email=email)
    await services.user_service.update_user_details(user_id, user_data)
    return RedirectResponse(url="/admin/users", status_code=status.HTTP_302_FOUND)


@router.get("/{user_id}/delete", name="user:delete")
@catch_error
@login_required("admin")
async def delete_user(request:Request, user_id: str):
    await services.user_service.remove_user(user_id)
    return RedirectResponse(url="/admin/users", status_code=status.HTTP_302_FOUND)


@router.get("/{user_id}/toggle", name="user:toggle_status")
@catch_error
@login_required("admin")
async def toggle_user_status(request: Request, user_id: str):
    user = await services.user_service.get_user_by_id(user_id)
    if user:
        await services.user_service.change_user_status(user_id, not user.is_active)
    return RedirectResponse(url="/admin/users", status_code=status.HTTP_302_FOUND)
