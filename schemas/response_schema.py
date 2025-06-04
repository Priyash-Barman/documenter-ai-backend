# schemas/response_schema.py
from typing import Generic, TypeVar, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import status

T = TypeVar('T')

class PaginationData(BaseModel):
    current_page: int
    next_page: Optional[int]
    total_pages: int
    total_items: int

class SuccessResponse(BaseModel):
    status: str = "success"
    message: Optional[str] = None

class SuccessData(SuccessResponse, Generic[T]):
    data: Optional[T] = None

class SuccessDataPaginated(SuccessResponse, Generic[T]):
    data: Optional[List[T]] = None
    pagination: Optional[PaginationData] = None

class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    data: Optional[Dict[str, Any]] = None

    @staticmethod
    def set(message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        response = {
            "status": "error",
            "message": message,
        }
        if data is not None:
            response["data"] = data
        return response

    @staticmethod
    def get_common_responses() -> Dict[int, Dict[str, Any]]:
        """Returns a dictionary of common error responses for all routes"""
        return {
            status.HTTP_400_BAD_REQUEST: {
                "description": "Bad Request",
                "content": {
                    "application/json": {
                        "example": ErrorResponse.set("Invalid request data")
                    }
                }
            },
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Unauthorized",
                "content": {
                    "application/json": {
                        "example": ErrorResponse.set("Authentication required")
                    }
                }
            },
            status.HTTP_403_FORBIDDEN: {
                "description": "Forbidden",
                "content": {
                    "application/json": {
                        "example": ErrorResponse.set("Permission denied")
                    }
                }
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "Not Found",
                "content": {
                    "application/json": {
                        "example": ErrorResponse.set("Resource not found")
                    }
                }
            },
            status.HTTP_409_CONFLICT: {
                "description": "Conflict",
                "content": {
                    "application/json": {
                        "example": ErrorResponse.set("Resource conflict occurred")
                    }
                }
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY: {
                "description": "Validation Error",
                "content": {
                    "application/json": {
                        "example": ErrorResponse.set("Validation error", {
                            "detail": [
                                {
                                    "loc": ["body", "field_name"],
                                    "msg": "field required",
                                    "type": "value_error.missing"
                                }
                            ]
                        })
                    }
                }
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Internal Server Error",
                "content": {
                    "application/json": {
                        "example": ErrorResponse.set("Internal server error")
                    }
                }
            }
        }

    @staticmethod
    def not_found(resource: str = "Resource", details: Optional[Dict] = None) -> Dict:
        """Standard 404 response"""
        return ErrorResponse.set(f"{resource} not found", details)

    @staticmethod
    def forbidden(action: str = "perform this action", details: Optional[Dict] = None) -> Dict:
        """Standard 403 response"""
        return ErrorResponse.set(f"Not authorized to {action}", details)

    @staticmethod
    def bad_request(message: str = "Invalid request", details: Optional[Dict] = None) -> Dict:
        """Standard 400 response"""
        return ErrorResponse.set(message, details)