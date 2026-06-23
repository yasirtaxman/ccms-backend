"""Create canonical roles and safely bootstrap a CCMS System Administrator."""
import argparse
import os
from sqlalchemy import select
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User
from app.services.user_service import validate_password

ROLE_NAMES=("Admin","Manager","Data Entry Operator","Viewer")

def bootstrap(username: str | None=None, password: str | None=None) -> None:
    username=username or settings.ADMIN_USERNAME or os.getenv("ADMIN_USERNAME")
    password=password or settings.ADMIN_PASSWORD or os.getenv("ADMIN_PASSWORD")
    if not username: raise SystemExit("ADMIN_USERNAME is required")
    if not password:
        if settings.ENVIRONMENT.lower()=="production": raise SystemExit("ADMIN_PASSWORD is required in production")
        password="DevSecure9!Key"
        print("WARNING: using local development admin password; set ADMIN_PASSWORD before deployment.")
    validate_password(password,username,password)
    with SessionLocal() as db:
        roles={}
        for name in ROLE_NAMES:
            role=db.scalar(select(Role).where(Role.name==name))
            if role is None: role=Role(name=name); db.add(role); db.flush()
            roles[name]=role
        user=db.scalar(select(User).where(User.username==username))
        if user is None:
            user=User(username=username,full_name="System Administrator",email=None,password_hash=hash_password(password),is_active=True,force_password_change=True)
            db.add(user); db.flush()
        if roles["Admin"] not in user.roles: user.roles.append(roles["Admin"])
        user.is_active=True; db.commit()
        print(f"Admin role assigned to '{username}'.")

if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("username",nargs="?"); parser.add_argument("--password")
    args=parser.parse_args(); bootstrap(args.username,args.password)
