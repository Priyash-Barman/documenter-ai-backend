# routes/manage_history_routes.py
from fastapi import APIRouter, Request, Query, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from decorators.authenticator import login_required
from services import services
from decorators.catch_error import catch_error
from utils.logger import logger

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
    
    # Get conversion statistics for dashboard display
    conversion_stats = await services.history_service.get_conversion_history_stats()

    return templates.TemplateResponse("admin/histories/list.html", {
        "request": request,
        "histories": histories,
        "req_from": req_from if req_from != "null" else None,
        "user_id": user_id if user_id != "null" else None,
        "app_id": app_id if app_id != "null" else None,
        "pagination": pagination,
        "conversion_stats": conversion_stats
    })

@router.get("/{history_id}", name="history:detail")
@catch_error
@login_required("admin")
async def history_detail(request: Request, history_id: str):
    history = await services.history_service.get_history_by_id(history_id)
    if not history:
        return RedirectResponse(url="/admin/histories", status_code=status.HTTP_302_FOUND)

    # Get detailed conversion info (since we're reading from conversion_history, we already have it)
    detailed_conversion = None
    try:
        from bson import ObjectId
        detailed_conversion_doc = await services.converter_service.history_collection.find_one({
            "_id": ObjectId(history_id)
        })
        if detailed_conversion_doc:
            detailed_conversion_doc["_id"] = str(detailed_conversion_doc["_id"])
            detailed_conversion = detailed_conversion_doc
    except Exception as e:
        logger.error(f"Error getting detailed conversion: {str(e)}")

    return templates.TemplateResponse("admin/histories/detail.html", {
        "request": request,
        "history": history,
        "detailed_conversion": detailed_conversion
    })