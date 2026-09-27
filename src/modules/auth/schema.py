from pydantic import BaseModel, EmailStr, Field

from src.modules.users.schema import UserResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=12,
    )


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse





class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(pattern=r"^\d{6}$")
    new_password: str = Field(min_length=8, max_length=12)


class MessageResponse(BaseModel):
    message: str