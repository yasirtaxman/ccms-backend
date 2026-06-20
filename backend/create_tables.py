from app.core.database import engine, Base

from app.models.child import Child
from app.models.document import Document

Base.metadata.create_all(bind=engine)

print("Tables created successfully.")