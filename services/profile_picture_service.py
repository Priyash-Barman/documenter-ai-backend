# services/profile_picture_service.py
import os
import uuid
from typing import Optional
from PIL import Image
import io
from fastapi import UploadFile, HTTPException, status
from utils.logger import logger

class ProfilePictureService:
    def __init__(self, upload_dir: str = "static/uploads/profile_pictures"):
        self.upload_dir = upload_dir
        # Create directory if it doesn't exist
        os.makedirs(self.upload_dir, exist_ok=True)
        
    async def save_profile_picture(self, file: UploadFile, user_id: str) -> str:
        """
        Save profile picture and return the file path
        """
        # Validate file type
        if not self._is_valid_image_type(file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only JPEG, PNG, and GIF images are allowed."
            )
            
        # Validate file size (max 5MB)
        if file.size and file.size > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size too large. Maximum allowed size is 5MB."
            )
            
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        filename = f"{user_id}_{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(self.upload_dir, filename)
        
        try:
            # Process and resize image
            contents = await file.read()
            image = Image.open(io.BytesIO(contents))
            
            # Convert to RGB if necessary (for PNG with transparency)
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
                
            # Resize image to max 500x500 while maintaining aspect ratio
            image.thumbnail((500, 500), Image.Resampling.LANCZOS)
            
            # Save processed image
            rgb_im = image.convert('RGB')
            rgb_im.save(file_path, format='JPEG', quality=85, optimize=True)
            
            # Return relative path for web access
            return f"/{self.upload_dir}/{filename}"
            
        except Exception as e:
            logger.error(f"Error saving profile picture: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process profile picture"
            )
            
    def _is_valid_image_type(self, file: UploadFile) -> bool:
        """
        Check if the uploaded file is a valid image type
        """
        valid_types = ['image/jpeg', 'image/png', 'image/gif']
        return file.content_type in valid_types
        
    def delete_profile_picture(self, file_path: str) -> bool:
        """
        Delete profile picture file
        """
        try:
            if file_path and os.path.exists(file_path.lstrip('/')):
                os.remove(file_path.lstrip('/'))
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting profile picture: {str(e)}")
            return False
            
    def get_default_avatar_url(self) -> str:
        """
        Get default avatar URL
        """
        return "/static/img/default-avatar.png"