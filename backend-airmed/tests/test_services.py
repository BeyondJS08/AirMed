def test_create_service_as_professional(client, professional_token):
    response = client.post(
        "/api/v1/services/",
        headers={"Authorization": f"Bearer {professional_token}"},
        json={
            "name": "General Checkup",
            "description": "A standard medical checkup",
            "duration_minutes": 30,
            "price": 150.0,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "General Checkup"
    assert data["duration_minutes"] == 30
    assert data["price"] == 150.0
    assert "id" in data


def test_create_service_as_non_professional(client, user_token):
    response = client.post(
        "/api/v1/services/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "name": "Checkup",
            "duration_minutes": 30,
        },
    )
    assert response.status_code == 403


def test_create_service_unauthenticated(client):
    response = client.post(
        "/api/v1/services/",
        json={"name": "Checkup", "duration_minutes": 30},
    )
    assert response.status_code == 401


def test_list_services(client, professional_token):
    client.post(
        "/api/v1/services/",
        headers={"Authorization": f"Bearer {professional_token}"},
        json={"name": "Checkup", "duration_minutes": 30},
    )
    response = client.get(
        "/api/v1/services/",
        headers={"Authorization": f"Bearer {professional_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_get_service_by_id(client, professional_token):
    create_resp = client.post(
        "/api/v1/services/",
        headers={"Authorization": f"Bearer {professional_token}"},
        json={"name": "Checkup", "duration_minutes": 30},
    )
    service_id = create_resp.json()["id"]

    response = client.get(
        f"/api/v1/services/{service_id}",
        headers={"Authorization": f"Bearer {professional_token}"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Checkup"


def test_get_service_not_found(client, professional_token):
    response = client.get(
        "/api/v1/services/9999",
        headers={"Authorization": f"Bearer {professional_token}"},
    )
    assert response.status_code == 404


def test_update_service_by_owner(client, professional_token):
    create_resp = client.post(
        "/api/v1/services/",
        headers={"Authorization": f"Bearer {professional_token}"},
        json={"name": "Checkup", "duration_minutes": 30},
    )
    service_id = create_resp.json()["id"]

    response = client.put(
        f"/api/v1/services/{service_id}",
        headers={"Authorization": f"Bearer {professional_token}"},
        json={"name": "Extended Checkup", "duration_minutes": 45},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Extended Checkup"
    assert response.json()["duration_minutes"] == 45


def test_update_service_not_owner(client, professional_token, user_token):
    create_resp = client.post(
        "/api/v1/services/",
        headers={"Authorization": f"Bearer {professional_token}"},
        json={"name": "Checkup", "duration_minutes": 30},
    )
    service_id = create_resp.json()["id"]

    response = client.put(
        f"/api/v1/services/{service_id}",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"name": "Hacked"},
    )
    assert response.status_code == 403


def test_delete_service_by_owner(client, professional_token):
    create_resp = client.post(
        "/api/v1/services/",
        headers={"Authorization": f"Bearer {professional_token}"},
        json={"name": "Checkup", "duration_minutes": 30},
    )
    service_id = create_resp.json()["id"]

    response = client.delete(
        f"/api/v1/services/{service_id}",
        headers={"Authorization": f"Bearer {professional_token}"},
    )
    assert response.status_code == 204


def test_delete_service_not_owner(client, professional_token, user_token):
    create_resp = client.post(
        "/api/v1/services/",
        headers={"Authorization": f"Bearer {professional_token}"},
        json={"name": "Checkup", "duration_minutes": 30},
    )
    service_id = create_resp.json()["id"]

    response = client.delete(
        f"/api/v1/services/{service_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403
