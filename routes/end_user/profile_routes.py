# routes/end_user/profile_routes.py
from fastapi import APIRouter, Request, Form, HTTPException, status, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional
import os

from decorators.authenticator import login_required
from decorators.catch_error import catch_error
from services import services
from services.profile_picture_service import ProfilePictureService
from schemas.user_schema import UserProfileUpdate
from schemas.profile_schema import ProfileView, ProfileUpdateResponse
from utils.logger import logger

router = APIRouter(prefix="/profile")
templates = Jinja2Templates(directory="templates")

# Initialize profile picture service
profile_picture_service = ProfilePictureService()

@router.get("/", name="profile:view")
@catch_error
@login_required("end_user")
async def view_profile(request: Request):
    """Display user's profile page"""
    try:
        user = request.state.user
        # Always fetch fresh profile data
        profile = await services.user_service.get_user_profile(user.id)
        
        if not profile:
            return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

        return templates.TemplateResponse("end_user/profile.html", {
            "request": request,
            "user": user,
            "profile": profile
        })

    except Exception as e:
        logger.error(f"Error loading profile: {str(e)}")
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@router.get("/edit", name="profile:edit_form")
@catch_error
@login_required("end_user")
async def edit_profile_form(request: Request):
    """Display profile edit form"""
    try:
        user = request.state.user
        profile = await services.user_service.get_user_profile(user.id)
        
        if not profile:
            return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

        return templates.TemplateResponse("end_user/profile_edit.html", {
            "request": request,
            "user": user,
            "profile": profile
        })

    except Exception as e:
        logger.error(f"Error loading profile edit form: {str(e)}")
        return RedirectResponse(url="/profile", status_code=status.HTTP_302_FOUND)

@router.post("/update", name="profile:update")
@catch_error
@login_required("end_user")
async def update_profile(
    request: Request,
    full_name: str = Form(...),
    profile_picture: UploadFile = File(None)
):
    """Handle profile update form submission"""
    try:
        user = request.state.user
        profile_picture_path = None
        
        # Handle profile picture upload if provided
        if profile_picture and profile_picture.filename:
            try:
                profile_picture_path = await profile_picture_service.save_profile_picture(profile_picture, user.id)
            except HTTPException as e:
                # If there's an error with the profile picture, still update the name
                logger.warning(f"Profile picture upload failed: {str(e.detail)}")
                # We'll continue with just updating the name
            except Exception as e:
                logger.error(f"Unexpected error during profile picture upload: {str(e)}")
        
        # Create update data
        profile_data = UserProfileUpdate(
            full_name=full_name.strip() if full_name else None
        )
        
        # Update profile (name only)
        updated_profile = await services.user_service.update_user_profile(user.id, profile_data)
        
        # Update profile picture separately if it was uploaded
        if profile_picture_path and updated_profile:
            updated_profile = await services.user_service.update_profile_picture(user.id, profile_picture_path)
        
        if not updated_profile:
            return templates.TemplateResponse("end_user/profile_edit.html", {
                "request": request,
                "user": user,
                "profile": user,
                "error": "Failed to update profile"
            })

        # Redirect to profile page with success parameter
        return RedirectResponse(url="/profile?updated=true", status_code=status.HTTP_302_FOUND)

    except ValueError as e:
        # Handle validation errors (like duplicate email)
        profile = await services.user_service.get_user_profile(user.id)
        return templates.TemplateResponse("end_user/profile_edit.html", {
            "request": request,
            "user": user,
            "profile": profile,
            "error": str(e)
        })
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        profile = await services.user_service.get_user_profile(user.id)
        return templates.TemplateResponse("end_user/profile_edit.html", {
            "request": request,
            "user": user,
            "profile": profile,
            "error": "An unexpected error occurred"
        })

@router.post("/remove-picture", name="profile:remove_picture")
@catch_error
@login_required("end_user")
async def remove_profile_picture(request: Request):
    """Remove user's profile picture"""
    try:
        user = request.state.user
        
        # Get current user to get profile picture path
        current_user = await services.user_service.get_user_profile(user.id)
        if current_user and current_user.profile_picture:
            # Delete the file
            profile_picture_service.delete_profile_picture(current_user.profile_picture)
        
        # Remove profile picture from database
        updated_profile = await services.user_service.remove_profile_picture(user.id)
        
        if not updated_profile:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "Failed to remove profile picture"}
            )

        return JSONResponse(
            content={
                "success": True, 
                "message": "Profile picture removed successfully",
                "profile_picture": None
            }
        )

    except Exception as e:
        logger.error(f"Error removing profile picture: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "Internal server error"}
        )

# API endpoints for AJAX requests
@router.get("/api", name="profile:api_view")
@catch_error
@login_required("end_user")
async def get_profile_api(request: Request):
    """API endpoint to get user profile"""
    try:
        user = request.state.user
        profile = await services.user_service.get_user_profile(user.id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )

        profile_view = ProfileView(
            id=profile.id,
            full_name=profile.full_name,
            email=profile.email,
            role=profile.role,
            is_active=profile.is_active,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )

        return JSONResponse(content={
            "success": True,
            "profile": profile_view.dict()
        })

    except Exception as e:
        logger.error(f"Error getting profile via API: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "Internal server error"}
        )

@router.put("/api", name="profile:api_update")
@catch_error
@login_required("end_user")
async def update_profile_api(request: Request, profile_data: UserProfileUpdate):
    """API endpoint to update user profile"""
    try:
        user = request.state.user
        
        # Update profile
        updated_profile = await services.user_service.update_user_profile(user.id, profile_data)
        
        if not updated_profile:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ProfileUpdateResponse(
                    success=False,
                    message="Failed to update profile"
                ).dict()
            )

        profile_view = ProfileView(
            id=updated_profile.id,
            full_name=updated_profile.full_name,
            email=updated_profile.email,
            role=updated_profile.role,
            is_active=updated_profile.is_active,
            created_at=updated_profile.created_at,
            updated_at=updated_profile.updated_at
        )

        return JSONResponse(content=ProfileUpdateResponse(
            success=True,
            message="Profile updated successfully",
            profile=profile_view
        ).dict())

    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ProfileUpdateResponse(
                success=False,
                message=str(e)
            ).dict()
        )
    except Exception as e:
        logger.error(f"Error updating profile via API: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ProfileUpdateResponse(
                success=False,
                message="Internal server error"
            ).dict()
        )