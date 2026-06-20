from app.core.security import create_access_token, hash_password
from app.models.audit_log import AuditLog
from app.models.role import Role, UserRole
from app.models.user import User


def make_user(db, username: str, role_name: str, active: bool = True) -> User:
    user = User(
        full_name=f"{username} User",
        username=username,
        email=f"{username}@ccms.example",
        password_hash=hash_password("StrongPassword123!"),
        is_active=active,
    )
    role = Role(name=role_name)
    db.add_all([user, role])
    db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    db.refresh(user)
    return user


def login(client, username: str) -> str:
    response = client.post(
        "/auth/login",
        json={"username_or_email": username, "password": "StrongPassword123!"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_current_user_requires_valid_token_and_rejects_disabled_user(client, db_session):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer bad"}).status_code == 401

    disabled = make_user(db_session, "disabled", "Viewer", active=False)
    token = create_access_token({"sub": disabled.username, "user_id": disabled.id})
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_login_me_and_login_audit(client, db_session):
    user = make_user(db_session, "viewer", "Viewer")
    token = login(client, user.username)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["roles"] == ["Viewer"]
    assert db_session.query(AuditLog).filter_by(action="LOGIN", user_id=user.id).count() == 1


def test_admin_role_management_and_viewer_is_read_only(client, db_session):
    admin = make_user(db_session, "admin", "Admin")
    admin_headers = {"Authorization": f"Bearer {login(client, admin.username)}"}
    created = client.post("/roles", json={"name": "Case Worker"}, headers=admin_headers)
    assert created.status_code == 201
    assert client.get("/audit-logs", headers=admin_headers).status_code == 200

    viewer = make_user(db_session, "readonly", "Viewer")
    viewer_headers = {"Authorization": f"Bearer {login(client, viewer.username)}"}
    assert client.get("/children", headers=viewer_headers).status_code == 200
    assert client.post("/children", json={}, headers=viewer_headers).status_code == 403
    assert client.get("/roles", headers=viewer_headers).status_code == 403
