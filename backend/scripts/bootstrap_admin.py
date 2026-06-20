"""Create the canonical roles and assign Admin to an existing user."""

import argparse

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.role import Role, UserRole
from app.models.user import User

ROLE_NAMES = ("Admin", "Manager", "Data Entry Operator", "Viewer")


def bootstrap(username: str) -> None:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == username))
        if user is None:
            raise SystemExit(f"User '{username}' does not exist. Register it first.")

        roles: dict[str, Role] = {}
        for name in ROLE_NAMES:
            role = db.scalar(select(Role).where(Role.name == name))
            if role is None:
                role = Role(name=name)
                db.add(role)
                db.flush()
            roles[name] = role

        admin = roles["Admin"]
        assignment = db.scalar(
            select(UserRole).where(
                UserRole.user_id == user.id, UserRole.role_id == admin.id
            )
        )
        if assignment is None:
            db.add(UserRole(user_id=user.id, role_id=admin.id))
        db.commit()
        print(f"Admin role assigned to '{username}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("username", help="Existing CCMS username")
    bootstrap(parser.parse_args().username)
