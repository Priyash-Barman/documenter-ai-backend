from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from decorators.authenticator import login_required
from decorators.catch_error import catch_error
from services import services

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("")
@catch_error
@login_required("admin")
async def dashboard(request: Request):
    # Get dynamic dashboard statistics
    dashboard_stats = await services.history_service.get_dashboard_stats()
    recent_activity = await services.history_service.get_recent_activity_feed(limit=5)
    
    return templates.TemplateResponse("admin/dashboard/index.html", {
        "request": request,
        "stats": dashboard_stats,
        "recent_activity": recent_activity
    })

@router.get("/api/conversion-growth")
@catch_error
@login_required("admin")
async def get_conversion_growth_data(request: Request):
    """API endpoint to get 60-day conversion growth data for charts"""
    growth_data = await services.history_service.get_60_day_conversion_growth()
    return JSONResponse(content=growth_data)

@router.get("/api/dashboard-stats")
@catch_error
@login_required("admin")
async def get_dashboard_stats(request: Request):
    """API endpoint to get real-time dashboard statistics"""
    stats = await services.history_service.get_dashboard_stats()
    return JSONResponse(content=stats)