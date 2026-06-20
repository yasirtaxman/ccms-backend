from pydantic import BaseModel


class AdmissionChecklistResponse(BaseModel):
    child_id: str

    admission_form: bool
    affidavit: bool
    death_certificate: bool
    father_cnic: bool
    guardian_cnic: bool
    birth_certificate: bool
    child_photo: bool

    admission_complete: bool