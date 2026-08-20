from pydantic import BaseModel, ConfigDict, EmailStr


class UserRegisterSchema(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str

class UserCreatedResponse(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str

    model_config = ConfigDict(from_attributes=True)

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str

class ChangePasswordSchema(BaseModel):
    old_password: str
    new_password: str


class RefreshTokenSchema(BaseModel):
    refresh_token: str

class CheckEmailSchema(BaseModel):
    email: EmailStr

class RequestResetCodeSchema(BaseModel):
    email: EmailStr

class ResetPasswordSchema(BaseModel):
    email: EmailStr
    code: str
    new_password: str