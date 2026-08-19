from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, status, HTTPException
from app.users.models import User
from app.auth.interfaces.service import IAuthService
from .schemas import (UserRegisterSchema, UserCreatedResponse,UserLoginSchema,
                      ChangePasswordSchema, RefreshTokenSchema, RequestResetCodeSchema, ResetPasswordSchema)
from app.shared.dependencies import get_current_user

auth_router = APIRouter(prefix="/auth", tags=["Auth"], route_class=DishkaRoute)



@auth_router.post('/register', response_model=UserCreatedResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegisterSchema,
                        auth_service: FromDishka[IAuthService]):
    return await auth_service.register_user(user_data)


@auth_router.post('/login', response_model=dict, status_code=status.HTTP_200_OK)
async def login(user_data: UserLoginSchema,
                auth_service: FromDishka[IAuthService])-> dict:
    return await auth_service.login(user_data)


@auth_router.post('/logout', status_code=status.HTTP_204_NO_CONTENT)
async def logout(token: RefreshTokenSchema,
                 auth_service: FromDishka[IAuthService]):
    await auth_service.logout(token.refresh_token)


@auth_router.post('/refresh', response_model=dict, status_code=status.HTTP_200_OK)
async def refresh(token: RefreshTokenSchema,
                  auth_service: FromDishka[IAuthService]):
    return await auth_service.refresh_new_token(token.refresh_token)



@auth_router.put('/change_password', response_model=dict, status_code=status.HTTP_200_OK)
async def change_password(password_data: ChangePasswordSchema,
                    current_user: Annotated[User, Depends(get_current_user)],
                    auth_service: FromDishka[IAuthService]):

    await auth_service.change_password(current_user, password_data)
    return {"message": "Password changed successfully!"}


@auth_router.post('/forgot_password',response_model=dict, status_code=status.HTTP_200_OK)
async def get_verification_code(email: RequestResetCodeSchema,
                                auth_service: FromDishka[IAuthService]):

    return await auth_service.request_reset_code(email.email)

@auth_router.post('/reset_password', response_model=dict, status_code=status.HTTP_200_OK)
async def reset_password(data: ResetPasswordSchema,
                        auth_service: FromDishka[IAuthService]):
    return await auth_service.reset_password(data.email, data.code, data.new_password)