from datetime import date

from app.models.audit_log import AuditLog
from tests.test_medical import headers, make_child, make_user


def indicator(client, auth, name: str):
    response = client.get("/development-indicators", headers=auth)
    assert response.status_code == 200, response.text
    item = next(row for row in response.json() if row["indicator_name"] == name)
    return item


def test_development_indicator_seed_and_activation(client, db_session):
    admin = make_user(db_session, "dev-admin", "Admin")
    auth = headers(admin)
    seeded = client.get("/development-indicators", headers=auth)
    assert seeded.status_code == 200, seeded.text
    assert len(seeded.json()) >= 105
    self_harm = indicator(client, auth, "Self-harm talk or gesture observed")
    assert self_harm["is_sensitive"] is True

    off = client.post(f"/development-indicators/{self_harm['id']}/deactivate", headers=auth)
    assert off.status_code == 200 and off.json()["is_active"] is False
    on = client.post(f"/development-indicators/{self_harm['id']}/activate", headers=auth)
    assert on.status_code == 200 and on.json()["is_active"] is True


def test_observation_workflow_permissions_sensitive_notes_and_pdf(client, db_session):
    admin = make_user(db_session, "dev-flow-admin", "Admin")
    warden = make_user(db_session, "dev-flow-warden", "Warden")
    viewer = make_user(db_session, "dev-flow-viewer", "Viewer")
    child = make_child(db_session, "DEV-CHILD")
    auth = headers(admin)
    hygiene = indicator(client, auth, "Personal cleanliness")
    support = indicator(client, auth, "Needs academic support")
    self_harm = indicator(client, auth, "Self-harm talk or gesture observed")

    payload = {
        "child_id": child.id,
        "observation_date": date.today().isoformat(),
        "observation_frequency": "Weekly",
        "observer_role": "Warden",
        "general_summary": "Observed tendency is stable with positive support needs.",
        "recommended_support": "Follow-up recommended through counselor review.",
        "private_notes": "Sensitive review note",
        "responses": [
            {"indicator_id": hygiene["id"], "value_number": 4},
            {"indicator_id": support["id"], "value_boolean": True},
            {"indicator_id": self_harm["id"], "value_boolean": True, "note": "Requires counselor review"},
        ],
    }
    created = client.post("/child-development-observations", json=payload, headers=headers(warden))
    assert created.status_code == 201, created.text
    observation_id = created.json()["id"]
    assert created.json()["urgent_flag"] is True

    submitted = client.post(f"/child-development-observations/{observation_id}/submit", headers=headers(warden))
    assert submitted.status_code == 200 and submitted.json()["review_status"] == "Submitted"
    assert client.post(f"/child-development-observations/{observation_id}/review", json={"review_status": "Reviewed"}, headers=headers(warden)).status_code == 403
    reviewed = client.post(f"/child-development-observations/{observation_id}/review", json={"review_status": "Needs Follow-up", "recommended_support": "Suggested support through counseling activities."}, headers=auth)
    assert reviewed.status_code == 200 and reviewed.json()["review_status"] == "Needs Follow-up"
    closed = client.post(f"/child-development-observations/{observation_id}/close", headers=auth)
    assert closed.status_code == 200 and closed.json()["review_status"] == "Closed"

    viewer_result = client.get(f"/child-development-observations/{observation_id}", headers=headers(viewer))
    assert viewer_result.status_code == 200
    assert viewer_result.json()["private_notes"] is None
    assert all(not row.get("indicator", {}).get("is_sensitive") for row in viewer_result.json()["responses"])

    for path in [f"/exports/child-development-profile/{child.id}.pdf", "/exports/child-development-observations.pdf", "/exports/monthly-development-summary.pdf", "/exports/child-talent-summary.pdf"]:
        response = client.get(path, headers=auth)
        assert response.status_code == 200, response.text
        assert response.content.startswith(b"%PDF")

    actions = {row.action for row in db_session.query(AuditLog).filter_by(module="CHILD_DEVELOPMENT")}
    assert {"CHILD_DEVELOPMENT_OBSERVATION_CREATED", "CHILD_DEVELOPMENT_OBSERVATION_SUBMITTED", "CHILD_DEVELOPMENT_OBSERVATION_REVIEWED", "CHILD_DEVELOPMENT_OBSERVATION_CLOSED"} <= actions


def test_monthly_missing_and_archive(client, db_session):
    admin = make_user(db_session, "dev-missing-admin", "Admin")
    child = make_child(db_session, "DEV-MISS")
    auth = headers(admin)
    missing = client.get(f"/reports/monthly-development-missing?month={date.today().month}&year={date.today().year}", headers=auth)
    assert missing.status_code == 200
    assert any(row["id"] == child.id for row in missing.json())
    assert any(row["child_id"] == child.id and row["child_code"] == child.child_id for row in missing.json())

    created = client.post("/child-development-observations", json={"child_id": child.id, "observation_date": date.today().isoformat(), "observation_frequency": "Monthly", "general_summary": "Current indicator recorded.", "responses": []}, headers=auth)
    assert created.status_code == 201, created.text
    missing_after = client.get(f"/reports/monthly-development-missing?month={date.today().month}&year={date.today().year}", headers=auth)
    assert all(row["id"] != child.id for row in missing_after.json())
    archived = client.post(f"/child-development-observations/{created.json()['id']}/archive", headers=auth)
    assert archived.status_code == 200 and archived.json()["review_status"] == "Archived"


def test_development_report_contracts(client, db_session):
    admin = make_user(db_session, "dev-report-admin", "Admin")
    child = make_child(db_session, "DEV-REPORT")
    auth = headers(admin)
    support = indicator(client, auth, "Needs academic support")
    talent = indicator(client, auth, "Computer skill interest")

    created = client.post(
        "/child-development-observations",
        json={
            "child_id": child.id,
            "observation_date": date.today().isoformat(),
            "observation_frequency": "Monthly",
            "general_summary": "Current development report observation.",
            "responses": [
                {"indicator_id": support["id"], "value_boolean": True},
                {"indicator_id": talent["id"], "value_number": 5},
            ],
        },
        headers=auth,
    )
    assert created.status_code == 201, created.text

    report = client.get(f"/reports/child-development?month={date.today().month}&year={date.today().year}", headers=auth)
    assert report.status_code == 200, report.text
    data = report.json()
    assert set(data) == {"summary", "observations", "missing_monthly_observations", "talent_summary"}
    assert {"reviewed_this_month", "missing_monthly", "needs_follow_up", "urgent_flags", "support_needs", "talent_indicators"} <= set(data["summary"])
    assert isinstance(data["observations"], list)
    assert isinstance(data["missing_monthly_observations"], list)
    assert isinstance(data["talent_summary"], list)

    missing = client.get(f"/reports/monthly-development-missing?month={date.today().month}&year={date.today().year}", headers=auth)
    assert missing.status_code == 200
    if missing.json():
        row = missing.json()[0]
        assert isinstance(row["child_id"], int)
        assert "child_code" in row

    talent_response = client.get(f"/reports/child-talent-summary?month={date.today().month}&year={date.today().year}", headers=auth)
    assert talent_response.status_code == 200
    rows = talent_response.json()
    assert any(row["child_id"] == child.id and row["child_code"] == child.child_id for row in rows)
    row = next(row for row in rows if row["child_id"] == child.id)
    assert isinstance(row["possible_areas_of_interest"], list)
    assert isinstance(row["positive_strengths"], list)
    assert isinstance(row["support_needs"], list)


def test_development_ai_summary_workflow_reports_and_exports(client, db_session):
    admin = make_user(db_session, "dev-ai-admin", "Admin")
    viewer = make_user(db_session, "dev-ai-viewer", "Viewer")
    child = make_child(db_session, "DEV-AI")
    auth = headers(admin)
    support = indicator(client, auth, "Needs confidence-building activities")
    talent = indicator(client, auth, "Computer skill interest")
    created = client.post(
        "/child-development-observations",
        json={
            "child_id": child.id,
            "observation_date": date.today().isoformat(),
            "observation_frequency": "Monthly",
            "general_summary": "Current indicator supports structured review.",
            "responses": [
                {"indicator_id": support["id"], "value_boolean": True},
                {"indicator_id": talent["id"], "value_number": 5},
            ],
        },
        headers=auth,
    )
    assert created.status_code == 201, created.text

    generated = client.post(f"/children/{child.id}/development-ai-summaries/generate?month={date.today().month}&year={date.today().year}", headers=auth)
    assert generated.status_code == 201, generated.text
    summary = generated.json()
    assert summary["approval_status"] == "Generated"
    assert "diagnosis" not in summary["overall_summary"].lower()
    summary_id = summary["id"]

    report = client.get("/reports/development-ai-summaries", headers=auth)
    assert report.status_code == 200
    assert any(row["id"] == summary_id and row["child_code"] == child.child_id for row in report.json())

    reviewed = client.post(f"/development-ai-summaries/{summary_id}/review", json={"internal_notes": "Manager reviewed for staff support."}, headers=auth)
    assert reviewed.status_code == 200 and reviewed.json()["approval_status"] == "Reviewed"
    approved = client.post(f"/development-ai-summaries/{summary_id}/approve", headers=auth)
    assert approved.status_code == 200 and approved.json()["approval_status"] == "Approved"

    latest = client.get(f"/children/{child.id}/development-ai-summaries/latest", headers=headers(viewer))
    assert latest.status_code == 200
    assert latest.json()["approval_status"] == "Approved"
    assert latest.json()["internal_notes"] is None

    for path in [f"/exports/development-ai-summary/{summary_id}.pdf", f"/exports/child-development-ai-summary/{child.id}.pdf", "/exports/development-ai-summaries.pdf"]:
        response = client.get(path, headers=auth)
        assert response.status_code == 200, response.text
        assert response.content.startswith(b"%PDF")


def test_behavior_support_plan_workflow_report_notes_and_exports(client, db_session):
    admin = make_user(db_session, "bsp-admin", "Admin")
    viewer = make_user(db_session, "bsp-viewer", "Viewer")
    child = make_child(db_session, "BSP-CHILD")
    auth = headers(admin)
    support = indicator(client, auth, "Needs confidence-building activities")
    created_observation = client.post(
        "/child-development-observations",
        json={
            "child_id": child.id,
            "observation_date": date.today().isoformat(),
            "observation_frequency": "Monthly",
            "general_summary": "Current support indicator recorded.",
            "responses": [{"indicator_id": support["id"], "value_boolean": True}],
        },
        headers=auth,
    )
    assert created_observation.status_code == 201, created_observation.text

    generated = client.post(f"/children/{child.id}/behavior-support-plans/generate", headers=auth)
    assert generated.status_code == 201, generated.text
    plan = generated.json()
    assert plan["plan_status"] == "Draft"
    assert plan["plan_code"].startswith("BSP-")
    assert "diagnosis" not in (plan["identified_behavior"] or "").lower()
    plan_id = plan["id"]

    note = client.post(
        f"/behavior-support-plans/{plan_id}/notes",
        json={"note_date": date.today().isoformat(), "note_type": "Progress Note", "progress_note": "Progress note recorded.", "follow_up_required": True, "next_step": "Follow-up required by staff."},
        headers=auth,
    )
    assert note.status_code == 201, note.text
    notes = client.get(f"/behavior-support-plans/{plan_id}/notes", headers=auth)
    assert notes.status_code == 200 and len(notes.json()) == 1

    active = client.post(f"/behavior-support-plans/{plan_id}/activate", headers=auth)
    assert active.status_code == 200 and active.json()["plan_status"] == "Active"
    report = client.get("/reports/behavior-support-plans", headers=auth)
    assert report.status_code == 200
    assert report.json()["summary"]["active_plans"] >= 1
    assert any(row["id"] == plan_id for row in report.json()["plans"])

    viewer_result = client.get(f"/behavior-support-plans/{plan_id}", headers=headers(viewer))
    assert viewer_result.status_code == 200
    assert viewer_result.json()["internal_notes"] is None

    for path in [f"/exports/behavior-support-plan/{plan_id}.pdf", f"/exports/child-behavior-support-plans/{child.id}.pdf", "/exports/behavior-support-plans.pdf"]:
        response = client.get(path, headers=auth)
        assert response.status_code == 200, response.text
        assert response.content.startswith(b"%PDF")
