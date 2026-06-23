from app.core.config import settings
from tests.test_user_admin import headers, make_user

def test_validation_error_standard_format(client,db_session):
    admin,_=make_user(db_session,"validationadmin","Admin")
    response=client.post("/users",json={},headers=headers(admin)); assert response.status_code==422
    body=response.json(); assert body["success"] is False and body["data"] is None and body["errors"]

def test_rate_limiting_disabled_then_enabled(client):
    original_enabled=settings.RATE_LIMIT_ENABLED; original_limit=settings.RATE_LIMIT_PER_MINUTE
    try:
        settings.RATE_LIMIT_ENABLED=False
        for _ in range(4): assert client.get("/").status_code==200
        settings.RATE_LIMIT_ENABLED=True; settings.RATE_LIMIT_PER_MINUTE=2
        statuses=[client.get("/").status_code for _ in range(3)]
        assert statuses[-1]==429
    finally:
        settings.RATE_LIMIT_ENABLED=original_enabled; settings.RATE_LIMIT_PER_MINUTE=original_limit
