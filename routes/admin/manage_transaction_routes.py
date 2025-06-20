# routes/manage_transaction_routes.py
from fastapi import APIRouter, Request, Query, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from decorators.authenticator import login_required
from services import services
from decorators.catch_error import catch_error

router = APIRouter(prefix="/transactions")
templates = Jinja2Templates(directory="templates")

@router.get("/", name="transaction:list")
@catch_error
@login_required("admin")
async def list_transactions(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    subscription_id: Optional[str] = Query(None)
):
    filters = {}
    if status and status.lower() != "null":
        filters["status"] = status.lower()
    if subscription_id and subscription_id.lower() != "null":
        filters["subscription_id"] = subscription_id

    transactions, pagination = await services.transaction_service.get_transactions(
        page=page, limit=limit, filters=filters
    )

    return templates.TemplateResponse("admin/transactions/list.html", {
        "request": request,
        "transactions": transactions,
        "status": status if status != "null" else None,
        "subscription_id": subscription_id if subscription_id != "null" else None,
        "pagination": pagination
    })

@router.get("/{tx_id}", name="transaction:detail")
@catch_error
@login_required("admin")
async def transaction_detail(request: Request, tx_id: str):
    transaction = await services.transaction_service.get_transaction_by_id(tx_id)
    if not transaction:
        return RedirectResponse(url="/admin/transactions", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("admin/transactions/detail.html", {
        "request": request,
        "transaction": transaction
    })

@router.get("/{tx_id}/update-status", name="transaction:update_status")
@catch_error
@login_required("admin")
async def update_transaction_status(request: Request, tx_id: str, tx_status: str):
    await services.transaction_service.update_transaction_status(tx_id, tx_status)
    return RedirectResponse(url=f"/admin/transactions/{tx_id}", status_code=status.HTTP_302_FOUND)