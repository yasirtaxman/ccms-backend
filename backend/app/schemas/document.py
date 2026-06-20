from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    child_id: int
    document_type: str
    original_filename: str
    stored_filename: str
    file_path: str
    is_verified: bool

    class Config:
        from_attributes = True