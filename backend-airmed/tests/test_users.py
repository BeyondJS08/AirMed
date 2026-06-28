def test_get_me_authenticated(client, user_token):
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "google_id" in data


def test_get_me_unauthenticated(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_get_me_invalid_token(client):
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalidtoken123"},
    )
    assert response.status_code == 401


def test_list_professionals_returns_only_professionals(client, db_session):
    from app.core.security import get_password_hash
    from app.models.user import User

    patient = User(email="patient@test.com", full_name="Patient", hashed_password=get_password_hash("pass"), is_professional=False, is_active=True)
    pro = User(email="pro@test.com", full_name="Professional", hashed_password=get_password_hash("pass"), is_professional=True, is_active=True)
    inactive_pro = User(email="inactive@test.com", full_name="Inactive Pro", hashed_password=get_password_hash("pass"), is_professional=True, is_active=False)
    db_session.add_all([patient, pro, inactive_pro])
    db_session.commit()

    response = client.get("/api/v1/users/professionals")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["email"] == "pro@test.com"


def test_list_professionals_empty(client):
    response = client.get("/api/v1/users/professionals")
    assert response.status_code == 200
    assert response.json() == []


def test_list_professionals_unauthorized(client):
    response = client.get("/api/v1/users/professionals")
    assert response.status_code == 200
