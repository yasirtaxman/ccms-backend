from pydantic import BaseModel, ConfigDict, Field, field_validator


class RoleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Role name cannot be blank")
        return value


class RoleResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class RoleAssignmentResponse(BaseModel):
    user_id: int
    role: RoleResponse
    message: str
