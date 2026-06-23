from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.permission import Permission
from app.models.role import Role

MODULE_ACTIONS={
"dashboard":["view"],"children":["view","create","update","delete","export","import"],"children.documents":["view","upload","verify","delete","export"],"daily_attendance":["view","create","update","bulk_mark","delete","export"],"visitors":["view","create","update","delete","verify","block","export"],"child_visits":["view","create","update","delete","approve","reject","check_in","check_out","cancel","export"],"sponsors":["view","create","update","delete","export"],"sponsorships":["view","create","update","delete","cancel","export"],"accommodation":["view","create","update","delete","allocate","transfer","vacate","export"],"medical":["view","create","update","delete","export"],"education":["view","create","update","delete","export"],"case_management":["view","create","update","delete","close","export"],"reports":["view","export"],"imports":["view","upload","preview","commit"],"users":["view","create","update","deactivate","reset_password","assign_roles","export"],"roles":["view","create","update","delete","assign_permissions"],"audit_logs":["view","export"],"system_status":["view"]}
PERMISSION_CATALOG=[f"{module}.{action}" for module,actions in MODULE_ACTIONS.items() for action in actions]
VIEW_PERMISSIONS=[value for value in PERMISSION_CATALOG if value.endswith(".view")]
DEFAULT_ROLE_PERMISSIONS={
"Admin":["*"],
"Manager":[value for value in PERMISSION_CATALOG if not value.startswith(("users.","roles.","audit_logs."))],
"Data Entry Operator":[value for value in PERMISSION_CATALOG if value.split(".")[-1] in {"view","create","update","upload","preview","bulk_mark","check_in","check_out","cancel","export"} and not value.startswith(("users.","roles.","audit_logs.","system_status."))],
"Viewer":VIEW_PERMISSIONS+["children.export","visitors.export","child_visits.export","sponsors.export","sponsorships.export","accommodation.export","medical.export","education.export","case_management.export","reports.export"],
"Warden":["dashboard.view","children.view","daily_attendance.view","daily_attendance.create","daily_attendance.update","daily_attendance.bulk_mark","child_visits.view","child_visits.create","child_visits.check_in","child_visits.check_out","visitors.view","accommodation.view"],
}

def role_names(user):return {role.name for role in user.roles}
def effective_permissions(user)->set[str]:
    if "Admin" in role_names(user):return {"*"}
    values=set()
    for role in user.roles:
        stored={permission.name for permission in getattr(role,"permissions",[]) or []}
        values.update(stored if role.permissions_configured else DEFAULT_ROLE_PERMISSIONS.get(role.name,stored))
    return values
def has_permission(user,name):
    values=effective_permissions(user);return "*" in values or name in values
def permission_or_403(user,name):
    if not has_permission(user,name):raise HTTPException(403,f"Permission required: {name}")
def seed_permissions(db:Session):
    existing={item.name:item for item in db.scalars(select(Permission)).all()}
    for name in PERMISSION_CATALOG:
        if name not in existing:
            module,action=name.rsplit(".",1);item=Permission(name=name,module=module,action=action,description=f"{action.replace('_',' ').title()} {module.replace('.',' ')}");db.add(item);existing[name]=item
    db.flush()
    for role in db.scalars(select(Role)).all():
        if role.name in DEFAULT_ROLE_PERMISSIONS and role.name!="Admin" and not role.permissions_configured:role.permissions=[existing[name] for name in DEFAULT_ROLE_PERMISSIONS[role.name] if name!="*"];role.permissions_configured=True
