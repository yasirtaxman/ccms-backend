from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ActiveStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class GenderType(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    MIXED = "Mixed"


class BedStatus(str, Enum):
    VACANT = "Vacant"
    OCCUPIED = "Occupied"
    RESERVED = "Reserved"
    MAINTENANCE = "Maintenance"


class AllocationStatus(str, Enum):
    ACTIVE = "Active"
    TRANSFERRED = "Transferred"
    VACATED = "Vacated"


class TrackedResponse(BaseModel):
    organization_id: int | None
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    deleted_by: int | None
    model_config = ConfigDict(from_attributes=True)


class BuildingCreate(BaseModel):
    building_code: str = Field(min_length=1, max_length=50, examples=["BLD-A"])
    building_name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    gender_type: GenderType
    status: ActiveStatus = ActiveStatus.ACTIVE
    model_config = ConfigDict(extra="forbid")


class BuildingUpdate(BaseModel):
    building_code: str | None = Field(default=None, min_length=1, max_length=50)
    building_name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    gender_type: GenderType | None = None
    status: ActiveStatus | None = None
    model_config = ConfigDict(extra="forbid")


class BuildingResponse(TrackedResponse):
    id: int
    building_code: str
    building_name: str
    description: str | None
    gender_type: GenderType
    status: ActiveStatus


class BlockCreate(BaseModel):
    building_id: int = Field(gt=0)
    block_code: str = Field(min_length=1, max_length=50)
    block_name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    status: ActiveStatus = ActiveStatus.ACTIVE
    model_config = ConfigDict(extra="forbid")


class BlockUpdate(BaseModel):
    block_code: str | None = Field(default=None, min_length=1, max_length=50)
    block_name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    status: ActiveStatus | None = None
    model_config = ConfigDict(extra="forbid")


class BlockResponse(TrackedResponse):
    id: int
    building_id: int
    block_code: str
    block_name: str
    description: str | None
    status: ActiveStatus


class FloorCreate(BaseModel):
    block_id: int = Field(gt=0)
    floor_no: int
    floor_name: str = Field(min_length=1, max_length=255)
    status: ActiveStatus = ActiveStatus.ACTIVE
    model_config = ConfigDict(extra="forbid")


class FloorUpdate(BaseModel):
    floor_no: int | None = None
    floor_name: str | None = Field(default=None, min_length=1, max_length=255)
    status: ActiveStatus | None = None
    model_config = ConfigDict(extra="forbid")


class FloorResponse(TrackedResponse):
    id: int
    block_id: int
    floor_no: int
    floor_name: str
    status: ActiveStatus


class RoomCreate(BaseModel):
    floor_id: int = Field(gt=0)
    room_code: str = Field(min_length=1, max_length=50)
    room_name: str = Field(min_length=1, max_length=255)
    capacity: int = Field(gt=0)
    gender_type: GenderType
    status: ActiveStatus = ActiveStatus.ACTIVE
    model_config = ConfigDict(extra="forbid")


class RoomUpdate(BaseModel):
    room_code: str | None = Field(default=None, min_length=1, max_length=50)
    room_name: str | None = Field(default=None, min_length=1, max_length=255)
    capacity: int | None = Field(default=None, gt=0)
    gender_type: GenderType | None = None
    status: ActiveStatus | None = None
    model_config = ConfigDict(extra="forbid")


class RoomResponse(TrackedResponse):
    id: int
    floor_id: int
    room_code: str
    room_name: str
    capacity: int
    gender_type: GenderType
    status: ActiveStatus


class BedCreate(BaseModel):
    room_id: int = Field(gt=0)
    bed_code: str = Field(min_length=1, max_length=50)
    bed_name: str = Field(min_length=1, max_length=255)
    status: BedStatus = BedStatus.VACANT
    model_config = ConfigDict(extra="forbid")


class BedUpdate(BaseModel):
    bed_code: str | None = Field(default=None, min_length=1, max_length=50)
    bed_name: str | None = Field(default=None, min_length=1, max_length=255)
    status: BedStatus | None = None
    model_config = ConfigDict(extra="forbid")


class BedResponse(TrackedResponse):
    id: int
    room_id: int
    bed_code: str
    bed_name: str
    status: BedStatus


class BedAllocationCreate(BaseModel):
    child_id: int = Field(gt=0)
    bed_id: int = Field(gt=0)
    allocation_date: date
    allocation_reason: str | None = None
    notes: str | None = None
    model_config = ConfigDict(extra="forbid")


class BedAllocationUpdate(BaseModel):
    allocation_reason: str | None = None
    notes: str | None = None
    model_config = ConfigDict(extra="forbid")


class BedAllocationResponse(BaseModel):
    id: int
    organization_id: int | None
    child_id: int
    bed_id: int
    allocation_date: date
    vacation_date: date | None
    allocation_reason: str | None
    vacation_reason: str | None
    status: AllocationStatus
    notes: str | None
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class BedTransferRequest(BaseModel):
    bed_id: int = Field(gt=0)
    transfer_date: date
    reason: str = Field(min_length=2)
    notes: str | None = None
    model_config = ConfigDict(extra="forbid")


class BedVacationRequest(BaseModel):
    vacation_date: date
    reason: str = Field(min_length=2)
    notes: str | None = None
    model_config = ConfigDict(extra="forbid")


class BedTransferResponse(BaseModel):
    previous_allocation: BedAllocationResponse
    new_allocation: BedAllocationResponse


class OccupancyResponse(BaseModel):
    scope_id: int | None = None
    scope_code: str
    scope_name: str
    total_beds: int
    occupied_beds: int
    vacant_beds: int
    reserved_beds: int
    maintenance_beds: int
    occupancy_percentage: float


class AccommodationDashboard(BaseModel):
    total_buildings: int
    total_blocks: int
    total_floors: int
    total_rooms: int
    total_beds: int
    occupied_beds: int
    vacant_beds: int
    reserved_beds: int
    maintenance_beds: int
    children_without_beds: int
    occupancy_percentage: float


class ChildWithoutBedResponse(BaseModel):
    id: int
    child_id: str
    full_name: str
    status: str
