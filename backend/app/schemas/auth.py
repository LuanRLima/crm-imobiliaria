from datetime import datetime

from pydantic import BaseModel, field_validator


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if "@" not in value:
            raise ValueError("Informe um e-mail válido.")
        return value.lower()


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_at: datetime
    user: UserResponse
