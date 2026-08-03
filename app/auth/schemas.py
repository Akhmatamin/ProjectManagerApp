from pydantic import BaseModel, EmailStr

class UserRegisterSchema(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str

class ChangePasswordSchema(BaseModel):
    old_password: str
    new_password: str


class RefreshTokenSchema(BaseModel):
    refresh_token: str

class ResetPasswordSchema(BaseModel):
    email: EmailStr
    new_password: str
    verifier_code: int