from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserAdminCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str
    confirm_password: str
    email: EmailStr | None = None
    full_name: str | None = Field(None, max_length=255)
    is_active: bool = True
    role_ids: list[int] = Field(default_factory=list)

class UserAdminUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(None, max_length=255)
    is_active: bool | None = None

class RoleAssignmentRequest(BaseModel): role_ids: list[int]
class PasswordResetRequest(BaseModel):
    new_password: str
    confirm_password: str
    force_password_change: bool = True
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

class UserAdminResponse(BaseModel):
    id: int
    username: str
    email: EmailStr | None
    full_name: str | None
    is_active: bool
    force_password_change: bool
    roles: list[str]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UserListResponse(BaseModel):
    data: list[UserAdminResponse]
    limit: int
    offset: int
    total: int

class UserPermissionsResponse(BaseModel):
    user_id: int
    username: str
    roles: list[str]
    effective_permissions: list[str]
