from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import base64
from fastapi import UploadFile, File, Form
import time
from decorators.authenticator import login_required
from decorators.catch_error import catch_error
from schemas.home_schema import ConversionResponse
from utils.logger import logger
from services import services

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
@login_required("end_user")
async def landing_page(request: Request):
    """Landing page with user info and logout button"""
    try:
        user = request.state.user

        return templates.TemplateResponse("end_user/home.html", {
            "request": request,
            "user": user,
        })

    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        response = RedirectResponse(url="/login")
        response.delete_cookie("access_token")
        return response


@router.post("/convert", response_model=ConversionResponse)
@catch_error
@login_required("end_user")
async def convert(
        request: Request,
        model: str = Form(...),
        image: UploadFile = File(...)
):
    start_time = time.time()

    # For now, just return the same image as base64
    image_data = await image.read()
    processed_image = await services.converter_service.convert_image(image_data, model)
    image_base64 = base64.b64encode(processed_image).decode('utf-8')

    return {
        "success": True,
        "message": "Conversion successful",
        "filename": image.filename,
        "digitized_image": image_base64,
        "processing_time": time.time() - start_time,
        "model_used": model
    }