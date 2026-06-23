from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True
    )
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    permissions_configured: Mapped[bool] = mapped_column(Boolean,default=False,nullable=False)

    users: Mapped[list["User"]] = relationship(
        secondary="user_roles",
        back_populates="roles",
        lazy="selectin",
    )
    permissions: Mapped[list["Permission"]] = relationship(secondary="role_permissions", back_populates="roles", lazy="selectin")


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id")
    )


from app.models.user import User  # noqa: E402  (resolves the relationship type)
from app.models.permission import Permission  # noqa: E402
