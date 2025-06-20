# routes/manage_api_doc_routes.py
from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import status
from typing import Optional

from decorators.authenticator import login_required
from services import services
from schemas.api_doc_schema import ApiDocCreate, ApiDocUpdate
from decorators.catch_error import catch_error

router = APIRouter(prefix="/api-docs")
templates = Jinja2Templates(directory="templates")

@router.get("/", name="api_doc:list")
@catch_error
@login_required("admin")
async def list_api_docs(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    is_active: Optional[str] = Query(None),
    method: Optional[str] = Query(None)
):
    filters = {}
    if is_active and is_active.lower() != "null":
        filters["is_active"] = is_active.lower() == "true"
    if method and method.lower() != "null":
        filters["method"] = method.upper()

    api_docs, pagination = await services.api_doc_service.get_api_docs(
        page=page, limit=limit, search=search, sort=sort, filters=filters
    )

    return templates.TemplateResponse("admin/api_docs/list.html", {
        "request": request,
        "api_docs": api_docs,
        "search": search,
        "sort": sort,
        "is_active": is_active if is_active != "null" else None,
        "method": method if method != "null" else None,
        "pagination": pagination
    })

@router.get("/create", name="api_doc:create_form")
@catch_error
@login_required("admin")
async def create_api_doc_form(request: Request):
    return templates.TemplateResponse("admin/api_docs/form.html", {
        "request": request,
        "api_doc": None,
        "form_action": "/api-docs/create",
        "form_method": "POST"
    })

@router.post("/create", name="api_doc:create")
@catch_error
@login_required("admin")
async def create_api_doc(
    request: Request,
    url: str = Form(...),
    method: str = Form(...),
    payload: str = Form(...),
    response: str = Form(...),
    authentication: str = Form(...),
    description: str = Form(...),
    demo_url: str = Form(...),
    is_active: bool = Form(False)
):
    api_doc_data = ApiDocCreate(
        url=url,
        method=method,
        payload=payload,
        response=response,
        authentication=authentication,
        description=description,
        demo_url=demo_url,
        created_by=str(request.state.user.id),
        is_active=is_active
    )
    await services.api_doc_service.create_new_api_doc(api_doc_data)
    return RedirectResponse(url="/admin/api-docs", status_code=status.HTTP_302_FOUND)

@router.get("/{doc_id}/edit", name="api_doc:edit_form")
@catch_error
@login_required("admin")
async def edit_api_doc_form(request: Request, doc_id: str):
    api_doc = await services.api_doc_service.get_api_doc_by_id(doc_id)
    if not api_doc:
        return RedirectResponse(url="/admin/api-docs", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("admin/api_docs/form.html", {
        "request": request,
        "api_doc": api_doc,
        "form_action": f"/api-docs/{doc_id}/edit",
        "form_method": "POST"
    })

@router.post("/{doc_id}/edit", name="api_doc:update")
@catch_error
@login_required("admin")
async def update_api_doc(
    request: Request,
    doc_id: str,
    url: str = Form(...),
    method: str = Form(...),
    payload: str = Form(...),
    response: str = Form(...),
    authentication: str = Form(...),
    description: str = Form(...),
    demo_url: str = Form(...),
    is_active: bool = Form(False)
):
    api_doc_data = ApiDocUpdate(
        url=url,
        method=method,
        payload=payload,
        response=response,
        authentication=authentication,
        description=description,
        demo_url=demo_url,
        is_active=is_active
    )
    await services.api_doc_service.update_api_doc(doc_id, api_doc_data)
    return RedirectResponse(url="/admin/api-docs", status_code=status.HTTP_302_FOUND)

@router.get("/{doc_id}/delete", name="api_doc:delete")
@catch_error
@login_required("admin")
async def delete_api_doc(request: Request, doc_id: str):
    await services.api_doc_service.remove_api_doc(doc_id)
    return RedirectResponse(url="/admin/api-docs", status_code=status.HTTP_302_FOUND)