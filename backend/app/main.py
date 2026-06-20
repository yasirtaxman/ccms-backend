from fastapi import FastAPI

from app.api.v1.children import router as children_router
from app.api.v1.documents import router as documents_router

app = FastAPI(
    title="AL ISLAH CMS",
    version="1.0.0"
)

# Child APIs
app.include_router(children_router)

# Document APIs
app.include_router(documents_router)


@app.get("/")
def root():
    return {
        "message": "AL ISLAH Child Management System API Running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }