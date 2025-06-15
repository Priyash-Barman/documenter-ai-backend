# routes/manage_subscription_routes.py
from fastapi import APIRouter, Request, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import status
from typing import Optional
from datetime import datetime

from services import services
from decorators.catch_error import catch_error

router = APIRouter(prefix="/subscriptions")
templates = Jinja2Templates(directory="templates")

@router.get("/", name="subscription:list")
@catch_error
async def list_subscriptions(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    app_id: Optional[str] = Query(None)
):
    filters = {}
    if status and status.lower() != "null":
        filters["status"] = status.lower()
    if user_id and user_id.lower() != "null":
        filters["user_id"] = user_id
    if app_id and app_id.lower() != "null":
        filters["app_id"] = app_id

    subscriptions, pagination = await services.subscription_service.get_subscriptions(
        page=page, limit=limit, filters=filters
    )

    return templates.TemplateResponse("admin/subscriptions/list.html", {
        "request": request,
        "subscriptions": subscriptions,
        "status": status if status != "null" else None,
        "user_id": user_id if user_id != "null" else None,
        "app_id": app_id if app_id != "null" else None,
        "pagination": pagination
    })

@router.get("/{sub_id}", name="subscription:detail")
@catch_error
async def subscription_detail(request: Request, sub_id: str):
    subscription = await services.subscription_service.get_subscription_by_id(sub_id)
    if not subscription:
        return RedirectResponse(url="/admin/subscriptions", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("admin/subscriptions/detail.html", {
        "request": request,
        "subscription": subscription
    })

@router.get("/{sub_id}/cancel", name="subscription:cancel")
@catch_error
async def cancel_subscription(sub_id: str):
    await services.subscription_service.cancel_subscription(sub_id, datetime.utcnow())
    return RedirectResponse(url=f"/admin/subscriptions/{sub_id}", status_code=status.HTTP_302_FOUND)