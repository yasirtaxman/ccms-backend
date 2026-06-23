from tests.test_user_admin import headers, make_user

def test_health_headers_openapi_and_admin_system_endpoints(client,db_session):
    health=client.get("/health"); assert health.status_code==200
    assert health.json()["data"]["status"]=="healthy"
    assert health.headers["x-request-id"]
    assert health.headers["x-content-type-options"]=="nosniff"
    assert health.headers["x-frame-options"]=="DENY"
    assert client.get("/openapi.json").status_code==200
    assert client.get("/system/readiness").status_code==401
    admin,_=make_user(db_session,"systemadmin","Admin"); auth=headers(admin)
    assert client.get("/system/readiness",headers=auth).status_code==200
    info=client.get("/system/info",headers=auth); assert info.status_code==200
    assert "secret" not in info.text.lower() and "password" not in info.text.lower()
