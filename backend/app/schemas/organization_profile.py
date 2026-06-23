from pydantic import BaseModel, Field, field_validator


class OrganizationProfileBase(BaseModel):
    organization_name: str = Field(default="Child Care Management System", min_length=2, max_length=255)
    short_name: str = Field(default="CCMS", min_length=2, max_length=80)
    address: str | None = Field(default=None, max_length=2000)
    city: str | None = Field(default=None, max_length=120)
    district: str | None = Field(default=None, max_length=120)
    province: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=80)
    email: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=255)
    registration_no: str | None = Field(default=None, max_length=120)
    ntn_or_tax_no: str | None = Field(default=None, max_length=120)
    report_footer_text: str | None = Field(default=None, max_length=500)
    report_watermark_text: str | None = Field(default=None, max_length=120)
    primary_color: str | None = Field(default=None, max_length=20)
    secondary_color: str | None = Field(default=None, max_length=20)
    authorized_signatory_name: str | None = Field(default=None, max_length=255)
    authorized_signatory_designation: str | None = Field(default=None, max_length=255)
    is_active: bool = True

    @field_validator("primary_color", "secondary_color")
    @classmethod
    def validate_color(cls, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        if not value.startswith("#") or len(value) not in {4, 7}:
            raise ValueError("Color must be a hex value such as #174A7E")
        return value.upper()


class OrganizationProfileUpdate(OrganizationProfileBase):
    pass


class OrganizationProfileResponse(OrganizationProfileBase):
    id: int | None = None
    logo_url: str | None = None

    model_config = {"from_attributes": True}
