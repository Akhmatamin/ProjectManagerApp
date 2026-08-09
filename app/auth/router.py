from fastapi import APIRouter, Depends, status
from dependency_injector.wiring import inject, Provide
from app.users.models import User
from app.auth.interfaces.service import IAuthService
from .schemas import (UserRegisterSchema, UserCreatedResponse,UserLoginSchema,
                      ChangePasswordSchema, RefreshTokenSchema, RequestResetCodeSchema, ResetPasswordSchema)
from app.shared.security import get_current_user
from app.shared.container import Container


auth_router = APIRouter(prefix="/auth", tags=["Auth"])



@auth_router.post('/register', response_model=UserCreatedResponse, status_code=status.HTTP_201_CREATED)
@inject
async def register_user(user_data: UserRegisterSchema, auth_service: IAuthService = Depends(Provide[Container.auth_service])):
    return await auth_service.register_user(user_data)


@auth_router.post('/login', response_model=dict, status_code=status.HTTP_200_OK)
@inject
async def login(user_data: UserLoginSchema, auth_service: IAuthService = Depends(Provide[Container.auth_service]))-> dict:
    return await auth_service.login(user_data)


@auth_router.post('/logout', status_code=status.HTTP_204_NO_CONTENT)
@inject
async def logout(token: RefreshTokenSchema, auth_service: IAuthService = Depends(Provide[Container.auth_service])):
    await auth_service.logout(token.refresh_token)


@auth_router.post('/refresh', response_model=dict, status_code=status.HTTP_200_OK)
@inject
async def refresh(token: RefreshTokenSchema, auth_service: IAuthService = Depends(Provide[Container.auth_service])):
    return await auth_service.refresh_new_token(token.refresh_token)



@auth_router.put('/change_password', response_model=dict, status_code=status.HTTP_200_OK)
@inject
async def change_password(password_data: ChangePasswordSchema,
                    current_user: User = Depends(get_current_user),
                    auth_service: IAuthService = Depends(Provide[Container.auth_service])):

    await auth_service.change_password(current_user, password_data)
    return {"message": "Password changed successfully!"}


@auth_router.post('/forgot_password',response_model=dict, status_code=status.HTTP_200_OK)
@inject
async def get_verification_code(email: RequestResetCodeSchema, auth_service: IAuthService = Depends(Provide[Container.auth_service])):
    return await auth_service.request_reset_code(email.email)


@auth_router.post('/reset_password', response_model=dict, status_code=status.HTTP_200_OK)
@inject
async def reset_password(data: ResetPasswordSchema,
                   auth_service: IAuthService = Depends(Provide[Container.auth_service])):
    return await auth_service.reset_password(data.email, data.code, data.new_password)