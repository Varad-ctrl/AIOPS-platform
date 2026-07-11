def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "SuperSecret123",
            "role": "viewer",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "newuser@example.com"
    assert body["role"] == "viewer"


def test_register_duplicate_email_fails(client):
    payload = {
        "email": "dupe@example.com",
        "full_name": "Dupe",
        "password": "SuperSecret123",
        "role": "viewer",
    }
    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 400


def test_login_success(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "full_name": "Login User",
            "password": "SuperSecret123",
            "role": "admin",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "SuperSecret123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body


def test_login_invalid_password(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpass@example.com",
            "full_name": "Wrong Pass",
            "password": "SuperSecret123",
            "role": "viewer",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpass@example.com", "password": "IncorrectPassword"},
    )
    assert response.status_code == 401


def test_protected_route_requires_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_protected_route_with_valid_token(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "me@example.com",
            "full_name": "Me User",
            "password": "SuperSecret123",
            "role": "viewer",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "me@example.com", "password": "SuperSecret123"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


def test_rbac_blocks_viewer_from_admin_route(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "vieweronly@example.com",
            "full_name": "Viewer Only",
            "password": "SuperSecret123",
            "role": "viewer",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "vieweronly@example.com", "password": "SuperSecret123"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/users", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
