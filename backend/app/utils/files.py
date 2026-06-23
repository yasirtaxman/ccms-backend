import re
from pathlib import Path
from fastapi import HTTPException, UploadFile
from app.core.config import settings

SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")

def sanitize_filename(filename: str | None) -> str:
    name=Path(filename or "").name; name=SAFE_NAME.sub("_",name).strip("._")
    if not name or len(name)>200: raise HTTPException(422,"Invalid filename")
    return name

def safe_upload_directory(*segments: str) -> Path:
    root=settings.upload_path; cleaned=[SAFE_NAME.sub("_",str(segment)).strip("._") for segment in segments]
    if any(not segment for segment in cleaned): raise HTTPException(422,"Invalid upload path")
    target=root.joinpath(*cleaned).resolve()
    if root != target and root not in target.parents: raise HTTPException(422,"Invalid upload path")
    target.mkdir(parents=True,exist_ok=True); return target

def enforce_upload_size(file: UploadFile) -> None:
    position=file.file.tell(); file.file.seek(0,2); size=file.file.tell(); file.file.seek(position)
    if size > settings.MAX_UPLOAD_SIZE_MB*1024*1024: raise HTTPException(413,f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit")
