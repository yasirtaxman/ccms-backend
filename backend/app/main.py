from fastapi import FastAPI

from app.api.v1.children import router as children_router
from app.api.v1.documents import router as documents_router
from app.api.v1.auth import router as auth_router

app = FastAPI(
    title="CCMS - Child Care Management System",
    version="1.0.0"
)

app.include_router(children_router)
app.include_router(documents_router)
app.include_router(auth_router)


@app.get("/")
def root():
    return {
        "message": "CCMS API Running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }