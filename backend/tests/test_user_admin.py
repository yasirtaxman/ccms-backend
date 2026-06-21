from app.core.security import create_access_token, hash_password
from app.models.audit_log import AuditLog
from app.models.role import Role, UserRole
from app.models.user import User

def make_user(db,username,role,password="StrongPassword123!"):
    user=User(username=username,email=f"{username}@example.com",full_name=f"{username} User",password_hash=hash_password(password),is_active=True)
    role_row=Role(name=role); db.add_all([user,role_row]); db.flush(); db.add(UserRole(user_id=user.id,role_id=role_row.id)); db.commit(); db.refresh(user); return user,role_row

def headers(user):
    token=create_access_token({"sub":user.username,"user_id":user.id}); return {"Authorization":f"Bearer {token}"}

def test_admin_user_lifecycle_roles_and_passwords(client,db_session):
    admin,admin_role=make_user(db_session,"sysadmin","Admin")
    manager=Role(name="Manager"); viewer=Role(name="Viewer"); db_session.add_all([manager,viewer]); db_session.commit()
    auth=headers(admin)
    payload={"username":"caseworker","password":"Secure9!Pass","confirm_password":"Secure9!Pass","email":"case@example.com","full_name":"Case Worker","role_ids":[manager.id]}
    created=client.post("/users",json=payload,headers=auth); assert created.status_code==201,created.text
    body=created.json(); assert body["roles"]==["Manager"]
    assert "password" not in body and "password_hash" not in body
    user_id=body["id"]
    assert client.post("/users",json=payload,headers=auth).status_code==409
    weak={**payload,"username":"weakuser","email":"weak@example.com","password":"password","confirm_password":"password"}
    assert client.post("/users",json=weak,headers=auth).status_code==422
    assigned=client.post(f"/users/{user_id}/roles",json={"role_ids":[viewer.id]},headers=auth); assert assigned.json()["roles"]==["Viewer"]
    assert client.post(f"/users/{user_id}/deactivate",headers=auth).status_code==200
    assert client.post("/auth/login",json={"username_or_email":"caseworker","password":"Secure9!Pass"}).status_code==403
    assert client.post(f"/users/{user_id}/activate",headers=auth).status_code==200
    reset=client.post(f"/users/{user_id}/reset-password",json={"new_password":"Reset9!Pass","confirm_password":"Reset9!Pass","force_password_change":True},headers=auth)
    assert reset.status_code==200 and reset.json()["force_password_change"] is True
    assert db_session.query(AuditLog).filter_by(module="USER_ADMINISTRATION").count()>=5

def test_last_admin_protected_permissions_and_self_password_change(client,db_session):
    admin,_=make_user(db_session,"onlyadmin","Admin"); auth=headers(admin)
    assert client.post(f"/users/{admin.id}/deactivate",headers=auth).status_code==409
    permissions=client.get("/users/me/permissions",headers=auth); assert permissions.status_code==200 and permissions.json()["effective_permissions"]==["*"]
    changed=client.post("/auth/change-password",json={"current_password":"StrongPassword123!","new_password":"Changed9!Pass","confirm_password":"Changed9!Pass"},headers=auth)
    assert changed.status_code==200
    assert client.post("/auth/login",json={"username_or_email":"onlyadmin","password":"Changed9!Pass"}).status_code==200

def test_non_admin_cannot_manage_users(client,db_session):
    viewer,_=make_user(db_session,"normalviewer","Viewer")
    assert client.get("/users",headers=headers(viewer)).status_code==403
