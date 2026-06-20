from app.core.database import engine, Base

from app.models.child import Child
from app.models.document import Document

from app.models.user import User
from app.models.role import Role, UserRole

Base.metadata.create_all(bind=engine)

print("Tables created successfully.")