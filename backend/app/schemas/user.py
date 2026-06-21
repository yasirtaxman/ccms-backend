from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    full_name: str | None
    username: str
    email: EmailStr | None
    password: str


class UserLogin(BaseModel):
    username_or_email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserResponse(BaseModel):
    id: int
    full_name: str
    username: str
    email: EmailStr
    is_active: bool

    model_config = {"from_attributes": True}


class CurrentUser(UserResponse):
    roles: list[str] = Field(default_factory=list)
