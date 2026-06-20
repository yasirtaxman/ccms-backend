from datetime import date
from pydantic import BaseModel


class ChildCreate(BaseModel):
    child_id: str
    admission_file_no: str

    full_name: str
    father_name: str
    grandfather_name: str
    mother_name: str

    gender: str
    date_of_birth: date

    guardian_name: str
    guardian_relationship: str
    guardian_cnic: str
    guardian_mobile: str

    current_address: str
    permanent_address: str

    village_mohallah: str
    union_council: str
    tehsil: str
    district: str
    province: str

    admission_date: date
    reason_for_admission: str

    status: str


class ChildUpdate(BaseModel):
    full_name: str
    father_name: str
    grandfather_name: str
    mother_name: str

    guardian_name: str
    guardian_relationship: str
    guardian_cnic: str
    guardian_mobile: str

    current_address: str
    permanent_address: str

    village_mohallah: str
    union_council: str
    tehsil: str
    district: str
    province: str

    reason_for_admission: str

    status: str