from datetime import date

from app.core.security import create_access_token, hash_password
from app.models.audit_log import AuditLog
from app.models.child import Child
from app.models.role import Role, UserRole
from app.models.user import User


def make_user(db, username: str, role_name: str) -> User:
    user = User(full_name=f"{username} User", username=username, email=f"{username}@ccms.example", password_hash=hash_password("StrongPassword123!"), is_active=True)
    role = db.query(Role).filter(Role.name == role_name).first() or Role(name=role_name)
    db.add_all([user, role]); db.flush(); db.add(UserRole(user_id=user.id, role_id=role.id)); db.commit(); db.refresh(user)
    return user


def headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token({'sub': user.username, 'user_id': user.id})}"}


def make_child(db, code: str) -> Child:
    child = Child(child_id=code, admission_file_no=f"AF-{code}", full_name=f"Child {code}", father_name="Father", grandfather_name="Grandfather", mother_name="Mother", gender="Male", date_of_birth=date(2015, 1, 1), guardian_name="Guardian", guardian_relationship="Uncle", guardian_cnic="42101-1234567-1", guardian_mobile="03001234567", current_address="Address", permanent_address="Address", village_mohallah="Area", union_council="UC", tehsil="Tehsil", district="District", province="Province", admission_date=date(2025, 1, 1), reason_for_admission="Support", status="Active")
    db.add(child); db.commit(); db.refresh(child); return child


def create_hierarchy(client, auth, *, capacity: int = 3, suffix: str = "A") -> dict:
    building = client.post("/buildings", json={"building_code": f"BLD-{suffix}", "building_name": f"Building {suffix}", "gender_type": "Male"}, headers=auth)
    assert building.status_code == 201
    block = client.post("/blocks", json={"building_id": building.json()["id"], "block_code": f"B-{suffix}", "block_name": f"Block {suffix}"}, headers=auth)
    assert block.status_code == 201
    floor = client.post("/floors", json={"block_id": block.json()["id"], "floor_no": 1, "floor_name": "Ground"}, headers=auth)
    assert floor.status_code == 201
    room = client.post("/rooms", json={"floor_id": floor.json()["id"], "room_code": f"R-{suffix}", "room_name": f"Room {suffix}", "capacity": capacity, "gender_type": "Male"}, headers=auth)
    assert room.status_code == 201
    return {"building": building.json(), "block": block.json(), "floor": floor.json(), "room": room.json()}


def create_bed(client, auth, room_id: int, code: str, status: str = "Vacant") -> dict:
    response = client.post("/beds", json={"room_id": room_id, "bed_code": code, "bed_name": code, "status": status}, headers=auth)
    assert response.status_code == 201
    return response.json()


def test_hierarchy_rbac_capacity_and_delete_guards(client, db_session):
    manager = make_user(db_session, "accommodation-manager", "Manager")
    auth = headers(manager)
    hierarchy = create_hierarchy(client, auth, capacity=1)
    room_id = hierarchy["room"]["id"]
    create_bed(client, auth, room_id, "BED-1")

    assert client.post("/beds", json={"room_id": room_id, "bed_code": "BED-2", "bed_name": "Bed 2"}, headers=auth).status_code == 409
    assert client.put(f"/rooms/{room_id}", json={"capacity": 0}, headers=auth).status_code == 422

    viewer = make_user(db_session, "accommodation-viewer", "Viewer")
    viewer_auth = headers(viewer)
    assert client.get("/buildings", headers=viewer_auth).status_code == 200
    assert client.post("/buildings", json={"building_code": "NO", "building_name": "No", "gender_type": "Mixed"}, headers=viewer_auth).status_code == 403
    assert client.delete(f"/rooms/{room_id}", headers=viewer_auth).status_code == 403

    admin = make_user(db_session, "accommodation-admin", "Admin")
    assert client.delete(f"/rooms/{room_id}", headers=headers(admin)).status_code == 409
    assert client.delete(f"/buildings/{hierarchy['building']['id']}", headers=headers(admin)).status_code == 409


def test_allocation_rules_transfer_vacation_reports_and_audit(client, db_session):
    manager = make_user(db_session, "allocation-manager", "Manager")
    auth = headers(manager)
    hierarchy = create_hierarchy(client, auth, capacity=3, suffix="ALLOC")
    room_id = hierarchy["room"]["id"]
    bed1 = create_bed(client, auth, room_id, "ALLOC-BED-1")
    bed2 = create_bed(client, auth, room_id, "ALLOC-BED-2")
    maintenance = create_bed(client, auth, room_id, "ALLOC-BED-3", "Maintenance")
    child1 = make_child(db_session, "ALLOC-C1")
    child2 = make_child(db_session, "ALLOC-C2")

    allocation_payload = {"child_id": child1.id, "bed_id": bed1["id"], "allocation_date": "2026-06-20", "allocation_reason": "Admission"}
    allocated = client.post("/bed-allocations", json=allocation_payload, headers=auth)
    assert allocated.status_code == 201
    allocation_id = allocated.json()["id"]
    assert client.get(f"/beds/{bed1['id']}", headers=auth).json()["status"] == "Occupied"

    assert client.post("/bed-allocations", json={**allocation_payload, "bed_id": bed2["id"]}, headers=auth).status_code == 409
    assert client.post("/bed-allocations", json={**allocation_payload, "child_id": child2.id}, headers=auth).status_code == 409
    assert client.post("/bed-allocations", json={**allocation_payload, "child_id": child2.id, "bed_id": maintenance["id"]}, headers=auth).status_code == 409

    assert client.put(f"/rooms/{room_id}", json={"status": "Inactive"}, headers=auth).status_code == 200
    assert client.post("/bed-allocations", json={**allocation_payload, "child_id": child2.id, "bed_id": bed2["id"]}, headers=auth).status_code == 409
    assert client.put(f"/rooms/{room_id}", json={"status": "Active"}, headers=auth).status_code == 200

    transfer = client.post(f"/bed-allocations/{allocation_id}/transfer", json={"bed_id": bed2["id"], "transfer_date": "2026-06-21", "reason": "Room arrangement"}, headers=auth)
    assert transfer.status_code == 200
    replacement_id = transfer.json()["new_allocation"]["id"]
    assert transfer.json()["previous_allocation"]["status"] == "Transferred"
    assert client.get(f"/beds/{bed1['id']}", headers=auth).json()["status"] == "Vacant"
    assert client.get(f"/beds/{bed2['id']}", headers=auth).json()["status"] == "Occupied"

    vacation = client.post(f"/bed-allocations/{replacement_id}/vacate", json={"vacation_date": "2026-06-22", "reason": "Discharge"}, headers=auth)
    assert vacation.status_code == 200
    assert vacation.json()["status"] == "Vacated"
    assert client.get(f"/beds/{bed2['id']}", headers=auth).json()["status"] == "Vacant"

    history = client.get("/bed-allocations", params={"child_id": child1.id}, headers=auth).json()
    assert {item["status"] for item in history} == {"Transferred", "Vacated"}
    dashboard = client.get("/dashboard/accommodation", headers=auth).json()
    assert dashboard["total_beds"] == 3 and dashboard["occupied_beds"] == 0
    assert dashboard["vacant_beds"] == 2 and dashboard["maintenance_beds"] == 1
    assert client.get("/reports/building-occupancy", headers=auth).status_code == 200
    assert client.get("/reports/children-without-beds", headers=auth).status_code == 200

    actions = [row.action for row in db_session.query(AuditLog).filter(AuditLog.module == "BED_ALLOCATIONS").order_by(AuditLog.id).all()]
    assert actions == ["BED_ALLOCATION", "BED_TRANSFER", "BED_VACATION"]


def test_data_entry_can_manage_and_duplicate_codes_are_rejected(client, db_session):
    operator = make_user(db_session, "accommodation-operator", "Data Entry Operator")
    auth = headers(operator)
    first = client.post("/buildings", json={"building_code": "DUP", "building_name": "First", "gender_type": "Mixed"}, headers=auth)
    assert first.status_code == 201
    assert client.post("/buildings", json={"building_code": "dup", "building_name": "Second", "gender_type": "Mixed"}, headers=auth).status_code == 409
    assert client.put(f"/buildings/{first.json()['id']}", json={"building_name": "Updated"}, headers=auth).status_code == 200
