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
        # Check if model is provided
        if not model or model.strip() == "":
            return {
                "success": False,
                "message": "Please select an AI model before converting.",
                "filename": image.filename,
                "digitized_image": "",
                "processing_time": time.time() - start_time,
                "model_used": model
            }

        # Check if model is supported
        supported_models = ["gemini", "gemini-flash", "gemini-flash-lite", "gemini-pro"]
        if model.lower() not in supported_models:
            return {
                "success": False,
                "message": f"Model '{model}' is not currently supported. Please select a valid model.",
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
            "message": f"Conversion successful! Document has been digitized using {model}.",
            "filename": image.filename,
            "digitized_image": image_base64,
            "processing_time": time.time() - start_time,
            "model_used": model
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Conversion error: {error_msg}")
        
        # Handle timeout errors specifically
        if "timeout" in error_msg.lower() or "504" in error_msg:
            model_name = model
            if model_name == "gemini-pro":
                suggestion = "The Gemini 2.5 Pro model is more powerful but slower. Try using 'gemini-2.5-flash' for faster results."
            else:
                suggestion = "The request timed out. Please try again or use a different model."
                
            return {
                "success": False,
                "message": f"Request timeout with {model_name}. {suggestion}",
                "filename": image.filename,
                "digitized_image": "",
                "processing_time": time.time() - start_time,
                "model_used": model
            }
        else:
            return {
                "success": False,
                "message": f"Conversion failed: {error_msg}",
                "filename": image.filename,
                "digitized_image": "",
                "processing_time": time.time() - start_time,
                "model_used": model
            }


@router.get("/history")
@catch_error
@login_required("end_user")
async def get_conversion_history(request: Request, page: int = 1, limit: int = 10):
    """Get user's conversion history with pagination"""
    try:
        user = request.state.user
        skip = (page - 1) * limit
        
        history, total_count = await services.converter_service.get_user_conversion_history(
            user.id, limit, skip
        )
        
        total_pages = (total_count + limit - 1) // limit  # Ceiling division
        
        return {
            "success": True,
            "history": history,
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        return {
            "success": False,
            "message": str(e),
            "history": [],
            "total": 0,
            "page": page,
            "limit": limit,
            "total_pages": 0,
            "has_next": False,
            "has_prev": False
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