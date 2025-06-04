from fastapi import APIRouter, Depends, HTTPException, Request

from decorators.authenticator import login_required
from schemas.user_schema import UserCreate, UserOut, Token, UserSchema
from fastapi.security import OAuth2PasswordRequestForm

from services import services

router = APIRouter()

@router.post("/register", response_model=UserOut)
async def register_user(user: UserCreate):
    return await services.auth_service.create_user(user)

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await services.auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = services.auth_service.create_access_token(data={"sub": user["email"]})
    return {"access_token": token, "token_type": "bearer"}

@router.get('/my-profile', response_model=UserSchema)
@login_required
async def my_profile(request: Request):
    user=request.state.user
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserSchema(**user)