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
    user = request.state.user

    try:

        if model.lower() != "gemini":
            return {
                "success": False,
                "message": f"Model '{model}' is not currently supported. Please select Gemini.",
                "filename": image.filename,
                "digitized_image": "",
                "processing_time": time.time() - start_time,
                "model_used": model
            }

        image_data = await image.read()
        
        processed_image = await services.converter_service.convert_image(
            image_data, model, user_id=user.id, filename=image.filename
        )
        
        image_base64 = base64.b64encode(processed_image).decode('utf-8')

        return {
            "success": True,
            "message": "Conversion successful! Document has been digitized using Gemini.",
            "filename": image.filename,
            "digitized_image": image_base64,
            "processing_time": time.time() - start_time,
            "model_used": model
        }

    except Exception as e:
        logger.error(f"Conversion error: {str(e)}")
        return {
            "success": False,
            "message": f"Conversion failed: {str(e)}",
            "filename": image.filename,
            "digitized_image": "",
            "processing_time": time.time() - start_time,
            "model_used": model
        }


@router.get("/history")
@catch_error
@login_required("end_user")
async def get_conversion_history(request: Request, limit: int = 10, skip: int = 0):
    """Get user's conversion history"""
    try:
        user = request.state.user
        history = await services.converter_service.get_user_conversion_history(
            user.id, limit, skip
        )
        
        return {
            "success": True,
            "history": history,
            "total": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        return {
            "success": False,
            "message": str(e),
            "history": []
        }


@router.get("/history/{conversion_id}")
@catch_error
@login_required("end_user")
async def get_conversion_details(request: Request, conversion_id: str):
    """Get detailed information about a specific conversion"""
    try:
        user = request.state.user
        details = await services.converter_service.get_conversion_details(
            conversion_id, user.id
        )
        
        if details:
            return {
                "success": True,
                "details": details
            }
        else:
            return {
                "success": False,
                "message": "Conversion not found"
            }
            
    except Exception as e:
        logger.error(f"Error getting conversion details: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }