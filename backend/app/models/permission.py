from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Permission(Base):
    __tablename__="permissions"
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(150),unique=True,index=True)
    module:Mapped[str]=mapped_column(String(100),index=True)
    action:Mapped[str]=mapped_column(String(100))
    description:Mapped[str|None]=mapped_column(String(255),nullable=True)
    roles:Mapped[list["Role"]]=relationship(secondary="role_permissions",back_populates="permissions")

class RolePermission(Base):
    __tablename__="role_permissions"
    __table_args__=(UniqueConstraint("role_id","permission_id",name="uq_role_permissions_role_permission"),)
    id:Mapped[int]=mapped_column(primary_key=True)
    role_id:Mapped[int]=mapped_column(ForeignKey("roles.id",ondelete="CASCADE"),index=True)
    permission_id:Mapped[int]=mapped_column(ForeignKey("permissions.id",ondelete="CASCADE"),index=True)

from app.models.role import Role  # noqa: E402
