# routes/user_routes.py
from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional

from services import services
from decorators.catch_error import catch_error
from schemas.user_schema import UserInDB, UserCreate, UserUpdate, UserStatusUpdate
from schemas.response_schema import SuccessResponse, ErrorResponse, PaginationData, SuccessData, SuccessDataPaginated
from defaults.enums import UserRole

router = APIRouter(prefix="/users")

@router.get("/", response_model=SuccessDataPaginated[UserInDB])
@catch_error
async def list_users(
        page: int = Query(1, ge=1),
        limit: int = Query(10, ge=1, le=100),
        search: Optional[str] = Query(None, min_length=2),
        sort: Optional[str] = Query(None),
        is_active: Optional[bool] = Query(None),
        role: Optional[UserRole] = Query(None)
):
    """
    Get paginated list of users with filtering and sorting
    """
    filters = {}
    if is_active is not None:
        filters['is_active'] = is_active
    if role:
        filters['role'] = role

    users, pagination = await services.user_service.get_users(
        page=page,
        limit=limit,
        search=search,
        sort=sort,
        filters=filters
    )

    return SuccessDataPaginated(
        message="Users retrieved successfully",
        data=users,
        pagination=PaginationData(**pagination)
    )


@router.get("/{user_id}", response_model=SuccessData[UserInDB])
@catch_error
async def get_user(user_id: str):
    """
    Get a specific user by ID
    """
    user = await services.user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                message="User not found",
                data={"user_id": user_id}
            ).dict()
        )
    return SuccessData(
        message="User retrieved successfully",
        data=user
    )


@router.post("/", response_model=SuccessData[UserInDB], status_code = status.HTTP_201_CREATED)
@catch_error
async def create_user(user_data: UserCreate):
    """
    Create a new user
    """
    try:
        user = await services.user_service.create_new_user(user_data)
        return SuccessData(
            message="User created successfully",
            data=user,
            status_code=status.HTTP_201_CREATED
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                message=str(e),
                data={"email": user_data.email}
            ).dict()
        )


@router.put("/{user_id}", response_model=SuccessData[UserInDB])
@catch_error
async def update_user(user_id: str, user_data: UserUpdate):
    """
    Update user details
    """
    updated_user = await services.user_service.update_user_details(user_id, user_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                message="User not found",
                data={"user_id": user_id}
            ).dict()
        )
    return SuccessData(
        message="User updated successfully",
        data=updated_user
    )


@router.patch("/{user_id}/status", response_model=SuccessData[UserInDB])
@catch_error
async def update_user_status(user_id: str, status_data: UserStatusUpdate):
    """
    Update user active status
    """
    updated_user = await services.user_service.change_user_status(user_id, status_data.is_active)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                message="User not found",
                data={"user_id": user_id}
            ).dict()
        )
    return SuccessData(
        message="User status updated successfully",
        data=updated_user
    )


@router.delete("/{user_id}", response_model=SuccessResponse)
@catch_error
async def delete_user(user_id: str):
    """
    Delete a user
    """
    deleted = await services.user_service.remove_user(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                message="User not found",
                data={"user_id": user_id}
            ).dict()
        )
    return SuccessResponse(
        message="User deleted successfully"
    )